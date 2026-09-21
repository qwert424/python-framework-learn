from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from app.core.config import db_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine

    if _engine is None:
        url = f"postgresql+asyncpg://{db_settings.user}:{db_settings.password}@{db_settings.host}:{db_settings.port}/{db_settings.name}"
        _engine = create_async_engine(
            url, pool_size=10, max_overflow=20, pool_pre_ping=True, echo=False
        )

    return _engine


_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,  # 明确指定使用异步 Session
            expire_on_commit=False,
        )

    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession]:
    session = get_session_factory()()  # 1. 创建 session（占用一条连接）
    session.begin()  # 2. 开启事务
    try:
        yield session  # 3. 业务逻辑在此执行
    except:  # 4a. 出错 → 回滚并继续抛出
        await session.rollback()
        raise
    else:
        await session.commit()  # 4b. 正常 → 提交
    finally:
        await session.close()  # 5. 关闭 session，归还连接
