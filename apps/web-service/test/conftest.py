"""pytest 测试脚手架：测试库生命周期 + 真实服务器 + 共享 fixtures。

会话流程：
    1. pytest_sessionstart：重建测试库 → 跑 Alembic 迁移建表 → 启动真实 FastAPI 服务
    2. 每个测试：通过 httpx 打真实 HTTP 接口，autouse 的 cleanup_db 保证用例间数据隔离
    3. pytest_sessionfinish：停服务器 → 删除测试库
"""

import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

import psycopg2
import pytest

# ─── 必须在任何 app 导入之前设置环境变量，让配置指向测试库 ───
os.environ.setdefault("DB_NAME", "learn_test_db")

from app.core.config import db_settings  # noqa: E402

TEST_SERVER_PORT = "18000"

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
WEB_SERVICE_DIR = Path(__file__).resolve().parent.parent

_server_process: subprocess.Popen | None = None
_log_file = None


@contextmanager
def _create_cur():
    """连接 postgres 默认库，用于创建/删除测试数据库（需 autocommit）。"""
    conn = psycopg2.connect(
        host=db_settings.host,
        port=db_settings.port,
        user=db_settings.user,
        password=db_settings.password,
        dbname="postgres",
    )
    conn.autocommit = True
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()
        conn.close()


def _start_server() -> None:
    """启动真实 FastAPI 服务进程，并轮询等待就绪。"""
    global _server_process, _log_file
    tmp_dir = WORKSPACE_ROOT / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    _log_file = open(tmp_dir / "test_server.log", "w", encoding="utf-8")
    _server_process = subprocess.Popen(
        [
            "uv",
            "run",
            "--package",
            "web-service",
            "fastapi",
            "dev",
            "apps/web-service/app/main.py",
            "--port",
            TEST_SERVER_PORT,
        ],
        cwd=str(WORKSPACE_ROOT),
        stdout=_log_file,
        stderr=subprocess.STDOUT,
    )

    import httpx

    for _ in range(50):
        try:
            resp = httpx.get(f"http://localhost:{TEST_SERVER_PORT}/docs")
            if resp.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.1)
    raise RuntimeError("测试服务器启动超时")


def _stop_server() -> None:
    global _server_process, _log_file
    if _server_process is not None:
        _server_process.terminate()
        _server_process.wait(timeout=10)
        _server_process = None
    if _log_file is not None:
        _log_file.close()
        _log_file = None


def pytest_sessionstart(session) -> None:
    """会话开始：重建测试数据库并跑迁移，然后启动服务。"""
    with _create_cur() as cur:
        cur.execute(
            "SELECT pg_terminate_backend(pg_stat_activity.pid) "
            "FROM pg_stat_activity "
            f"WHERE pg_stat_activity.datname = '{db_settings.name}' "
            "AND pid <> pg_backend_pid()"
        )
        cur.execute(f'DROP DATABASE IF EXISTS "{db_settings.name}"')
        cur.execute(f'CREATE DATABASE "{db_settings.name}"')

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(WEB_SERVICE_DIR / "migrations"))
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        f"postgresql://{db_settings.user}:{db_settings.password}"
        f"@{db_settings.host}:{db_settings.port}/{db_settings.name}",
    )
    command.upgrade(alembic_cfg, "head")

    _start_server()


def pytest_sessionfinish(session, exitstatus) -> None:
    """会话结束：停服务器并删除测试数据库。"""
    _stop_server()

    with _create_cur() as cur:
        cur.execute(
            "SELECT pg_terminate_backend(pg_stat_activity.pid) "
            "FROM pg_stat_activity "
            f"WHERE pg_stat_activity.datname = '{db_settings.name}' "
            "AND pid <> pg_backend_pid()"
        )
        cur.execute(f'DROP DATABASE IF EXISTS "{db_settings.name}"')


@pytest.fixture
def base_url() -> str:
    return f"http://localhost:{TEST_SERVER_PORT}"


@pytest.fixture
async def async_client():
    from httpx import AsyncClient

    async with AsyncClient(base_url=f"http://localhost:{TEST_SERVER_PORT}") as client:
        yield client


@pytest.fixture(autouse=True)
async def cleanup_db():
    """每个测试结束后清空所有表，保证用例之间数据隔离。"""
    yield

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    from app.model.base import Base

    url = (
        f"postgresql+asyncpg://{db_settings.user}:{db_settings.password}"
        f"@{db_settings.host}:{db_settings.port}/{db_settings.name}"
    )
    engine = create_async_engine(url, poolclass=NullPool, echo=False)

    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(
                text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE')
            )
    await engine.dispose()
