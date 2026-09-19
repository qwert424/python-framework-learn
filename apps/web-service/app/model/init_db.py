"""数据库初始化与连接测试脚本。

用法：python apps/web-service/app/model/init_db.py
"""

import asyncio

from sqlalchemy import text

from app.model import Base
from app.model.engine import get_engine


async def init_db() -> None:
    """根据 ORM 模型创建所有表。"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")


async def test_connection() -> None:
    """测试数据库连接。"""
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            print(f"✅ 连接成功！查询结果: {value}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
    finally:
        await engine.dispose()


async def main() -> None:
    await init_db()
    await test_connection()


if __name__ == "__main__":
    asyncio.run(main())
