"""原生 SQL 操作示例：演示直接拼接 SQL 的增删查。

用法：python apps/web-service/examples/raw_sql_demo.py
"""

import asyncio

from sqlalchemy import text

from app.core.database import get_engine
from app.model import Base


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")


async def raw_sql_insert() -> None:
    """直接用 SQL 字符串插入数据"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO product (name, description, brand) VALUES ('iPhone 16', '最新款智能手机', 'Apple')"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO product (name, description, brand) VALUES ('iPhone 15', '上一代旗舰', 'Apple')"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO product (name, description, brand) VALUES ('Galaxy S25', '三星旗舰', 'Samsung')"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO product (name, description, brand) VALUES ('Xiaomi 15', '性价比之选', 'Xiaomi')"
            )
        )
    print("✅ 数据插入完成")


async def search_products(keyword: str) -> None:
    """按关键字搜索商品——接受用户输入，参数化查询"""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT * FROM product WHERE name LIKE :keyword"),
            {"keyword": f"%{keyword}%"},
        )
        rows = result.fetchall()
        for row in rows:
            print(f"  [{row.id}] {row.name} - {row.brand}")


async def delete_product_by_id(product_id: int) -> None:
    """按 ID 删除商品——接受用户输入，拼接 SQL"""
    engine = get_engine()
    async with engine.begin() as conn:
        sql = f"DELETE FROM product WHERE id = :product_id"
        await conn.execute(text(sql), {"product_id": product_id})
    print(f"✅ 删除完成，id={product_id}")


async def main() -> None:
    await init_db()
    await raw_sql_insert()
    # 正常查询
    print("=== 搜索 'iPhone' ===")
    await search_products("%' OR 1=1 --")
    # 正常删除
    print("=== 删除 id=1 ===")
    await delete_product_by_id(1)
    print("=== 再次搜索 'iPhone' ===")
    await search_products("iPhone")


if __name__ == "__main__":
    asyncio.run(main())
