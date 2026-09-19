"""SQLAlchemy ORM 操作示例（对象方式增删改查）。

用法：python apps/web-service/examples/orm_sql.py
"""

import asyncio

from sqlalchemy import select

from app.core.database import get_engine, get_session_factory
from app.model import Base, Category, Product

session_factory = get_session_factory()


async def init_db() -> None:
    """删除并重建所有表，保证每次运行都是干净数据。"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")


async def orm_insert() -> None:
    """ORM 方式插入——创建对象，add 到 session"""
    async with session_factory.begin() as session:
        product = Product(
            name="iPhone 16",
            description="最新款智能手机",
            brand="Apple",
        )
        session.add(product)

        product2 = Product(
            name="iPhone 15",
            description="上一代旗舰",
            brand="Apple",
        )
        session.add(product2)

        category = Category(name="手机", description="移动通信设备")
        session.add(category)
    print("✅ ORM 插入完成")


async def orm_query() -> None:
    """ORM 方式查询——execute + scalars() 拿到对象列表"""
    async with session_factory() as session:
        stmt = select(Product).where(Product.name.like("%iPhone%"))
        result = await session.execute(stmt)
        # scalars() 返回模型实例，可直接访问属性
        products = result.scalars().all()
        for p in products:
            print(f"  [{p.id}] {p.name} - {p.brand}")


async def orm_update() -> None:
    """ORM 方式更新——查出对象，改属性，自动同步"""
    async with session_factory.begin() as session:
        stmt = select(Product).where(Product.id == 1)
        result = await session.execute(stmt)
        product = result.scalar_one()
        # 直接修改 Python 对象属性，session 提交时自动生成 UPDATE
        product.name = "iPhone 16 Pro"
    print("✅ ORM 更新完成")


async def orm_delete() -> None:
    """ORM 方式删除——查出对象，调用 session.delete()"""
    async with session_factory.begin() as session:
        stmt = select(Product).where(Product.id == 2)
        result = await session.execute(stmt)
        product = result.scalar_one()
        await session.delete(product)
    print("✅ ORM 删除完成")


async def main() -> None:
    await init_db()
    await orm_insert()
    print("=== 查询 ===")
    await orm_query()
    await orm_update()
    print("=== 查询（更新后） ===")
    await orm_query()
    await orm_delete()
    print("=== 查询（删除后） ===")
    await orm_query()


if __name__ == "__main__":
    asyncio.run(main())
