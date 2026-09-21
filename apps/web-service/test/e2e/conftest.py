import os
import subprocess
import time
import signal
import socket
from contextlib import contextmanager
from pathlib import Path

import httpx
import psycopg2
import pytest
from dotenv import load_dotenv

# ==========================
# 1. 路径与环境配置 (修正重点)
# ==========================

# 获取当前文件 (conftest.py) 的绝对路径
CURRENT_FILE = Path(__file__).resolve()

# 推导项目根目录和 Web Service 目录
# 假设结构: empty-project/apps/web-service/test/e2e/conftest.py
# parents[0] = e2e
# parents[1] = test
# parents[2] = web-service
# parents[3] = apps
# parents[4] = empty-project (ROOT)
WEB_SERVICE_DIR = CURRENT_FILE.parents[2]
PROJECT_ROOT = CURRENT_FILE.parents[4]

# 显式构建 migrations 路径
MIGRATIONS_DIR = WEB_SERVICE_DIR / "migrations"

# 【调试用】启动时打印路径，方便排查
print(f"[DEBUG] Project Root   : {PROJECT_ROOT}")
print(f"[DEBUG] Web Service Dir : {WEB_SERVICE_DIR}")
print(f"[DEBUG] Migrations Path : {MIGRATIONS_DIR}")
print(f"[DEBUG] Exists?         : {MIGRATIONS_DIR.exists()}")

if not MIGRATIONS_DIR.exists():
    raise FileNotFoundError(
        f"[ERROR] CRITICAL ERROR: Migrations directory not found at:\n{MIGRATIONS_DIR}\n"
        f"Please ensure 'alembic init migrations' was run in {WEB_SERVICE_DIR}"
    )

# 加载环境变量
ENV_FILE = PROJECT_ROOT / ".env.test"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # 如果找不到 .env.test，尝试加载根目录的 .env
    load_dotenv(PROJECT_ROOT / ".env")

os.environ["DB_NAME"] = "learn_e2e_test_db"

# 导入配置 (确保在设置完环境变量后导入)
from app.core.config import db_settings  # noqa: E402

TEST_SERVER_PORT = "18000"

_server_process: subprocess.Popen | None = None
_log_file_path = PROJECT_ROOT / "tmp" / "test_server.log"


# ==========================
# 2. 辅助函数
# ==========================


def _is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def _kill_process_on_port(port: int):
    """强制杀死占用端口的进程 (Windows/Linux 兼容)"""
    try:
        if os.name == "nt":  # Windows
            # netstat -ano | findstr :PORT
            res = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            for line in res.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    if pid.isdigit():
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", pid],
                            capture_output=True,
                        )
        else:  # Linux/Mac
            res = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True
            )
            if res.stdout:
                pids = res.stdout.strip().split("\n")
                for pid in pids:
                    if pid:
                        os.kill(int(pid), signal.SIGKILL)
        time.sleep(1)  # 等待端口释放
    except Exception:
        pass


@contextmanager
def _create_cur():
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


def _start_server():
    global _server_process

    # 启动前清理端口
    _kill_process_on_port(int(TEST_SERVER_PORT))

    tmp_dir = PROJECT_ROOT / "tmp"
    tmp_dir.mkdir(exist_ok=True)

    # 清空日志
    with open(_log_file_path, "w") as f:
        f.write("")

    print(f"[START] Starting server on port {TEST_SERVER_PORT}...")

    _server_process = subprocess.Popen(
        [
            "uv",
            "run",
            "--package",
            "web-service",
            "fastapi",
            "dev",
            "--no-reload",
            str(WEB_SERVICE_DIR / "app" / "main.py"),
            "--port",
            TEST_SERVER_PORT,
        ],
        cwd=str(PROJECT_ROOT),
        stdout=open(_log_file_path, "a"),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )

    # 等待服务就绪
    for i in range(60):
        if _server_process.poll() is not None:
            with open(_log_file_path, "r") as f:
                raise RuntimeError(f"Server crashed. Logs:\n{f.read()}")

        try:
            resp = httpx.get(f"http://localhost:{TEST_SERVER_PORT}/docs", timeout=2)
            if resp.status_code == 200:
                print("[OK] Server is ready.")
                return
        except httpx.ConnectError:
            pass

        time.sleep(0.5)

    _stop_server()
    raise RuntimeError("Server startup timeout. Check tmp/test_server.log")


def _stop_server():
    global _server_process
    if _server_process:
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_server_process.pid)],
                    capture_output=True,
                )
            else:
                os.killpg(os.getpgid(_server_process.pid), signal.SIGTERM)
            _server_process.wait(timeout=5)
        except Exception:
            pass
        finally:
            _server_process = None
    # 兑底：按端口再清理一次，防止 reload 子进程残留占用端口
    _kill_process_on_port(int(TEST_SERVER_PORT))


# ==========================
# 3. Pytest Hooks
# ==========================


def pytest_sessionstart(session):
    print("初始化测试数据库...")
    with _create_cur() as cur:
        # 1. 先终止所有到测试库的连接，删除旧库
        cur.execute(
            "SELECT pg_terminate_backend(pg_stat_activity.pid) "
            "FROM pg_stat_activity "
            f"WHERE pg_stat_activity.datname = '{db_settings.name}' "
            "AND pid <> pg_backend_pid()"
        )
        cur.execute(f'DROP DATABASE IF EXISTS "{db_settings.name}"')
        # 2. 全新创建测试库
        cur.execute(f'CREATE DATABASE "{db_settings.name}"')

    print("执行 Alembic 迁移...")
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        f"postgresql://{db_settings.user}:{db_settings.password}"
        f"@{db_settings.host}:{db_settings.port}/{db_settings.name}",
    )
    command.upgrade(alembic_cfg, "head")
    print("迁移完成，启动测试服务")
    _start_server()


def pytest_sessionfinish(session, exitstatus):
    print("停止测试服务...")
    _stop_server()
    # 3. 所有测试全部跑完后，最后一步才删除测试库
    print("测试全部结束，删除测试数据库...")
    with _create_cur() as cur:
        cur.execute(
            "SELECT pg_terminate_backend(pg_stat_activity.pid) "
            "FROM pg_stat_activity "
            f"WHERE pg_stat_activity.datname = '{db_settings.name}' "
            "AND pid <> pg_backend_pid()"
        )
        cur.execute(f'DROP DATABASE IF EXISTS "{db_settings.name}"')


# ==========================
# 4. Fixtures
# ==========================


@pytest.fixture
def base_url():
    return f"http://localhost:{TEST_SERVER_PORT}"


@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(
        base_url=f"http://localhost:{TEST_SERVER_PORT}"
    ) as client:
        yield client


REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"


async def _register_and_login(client: httpx.AsyncClient) -> str:
    await client.post(
        REGISTER_URL,
        json={"username": "e2etestuser", "password": "test123456"},
    )
    resp = await client.post(
        LOGIN_URL,
        json={"username": "e2etestuser", "password": "test123456"},
    )
    return resp.json()["data"]["access_token"]


@pytest.fixture
async def auth_headers(async_client):
    token = await _register_and_login(async_client)
    return {"Authorization": f"Bearer {token}"}


_SKIP_CLEANUP_TABLES = {"settinggroup", "setting"}


@pytest.fixture(autouse=True)
async def cleanup_db(async_client):
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
    try:
        async with engine.begin() as conn:
            tables_to_clean = [
                t
                for t in Base.metadata.sorted_tables
                if t.name not in _SKIP_CLEANUP_TABLES
            ]
            for table in reversed(tables_to_clean):
                try:
                    await conn.execute(
                        text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE')
                    )
                except Exception:
                    pass
    finally:
        await engine.dispose()
