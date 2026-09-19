"""异步 Session 使用示例（三种提交方式）。

用法：python apps/web-service/examples/session.py
"""

import asyncio

from sqlalchemy import insert

from app.core.database import get_engine, get_session_factory
from app.model import Base, Product

session_factory = get_session_factory()


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")


async def insert_with_session() -> None:
    session = session_factory()
    try:
        stmt = insert(Product).values(
            name="iPhone 16",
            description="最新款智能手机",
            brand="Apple",
        )
        await session.execute(stmt)
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()
    print("✅ 提交完成")


async def insert_with_manual_commit() -> None:
    """手动提交"""
    async with session_factory() as session:
        try:
            stmt = insert(Product).values(
                name="iPhone 16",
                description="最新款智能手机",
                brand="Apple",
            )
            await session.execute(stmt)
            await session.commit()
        except:
            await session.rollback()
            raise
    print("✅ 手动提交完成")


async def insert_with_auto_commit() -> None:
    """自动提交"""
    async with session_factory.begin() as session:
        stmt = insert(Product).values(
            name="iPhone 15",
            description="上一代旗舰",
            brand="Apple",
        )
        await session.execute(stmt)
    print("✅ 自动提交完成")


async def main() -> None:
    await init_db()
    await insert_with_session()
    await insert_with_manual_commit()
    await insert_with_auto_commit()


if __name__ == "__main__":
    asyncio.run(main())
