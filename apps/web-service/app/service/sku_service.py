from sqlalchemy import delete, exc as sa_exc, select, update

from app.exception.database import DatabaseException
from app.model.product import Product
from app.model.sku import Sku
from app.schemas.sku import SkuCreate, SkuResponse, SkuUpdate
from app.service.base import BaseService


class SkuService(BaseService):
    async def create_sku(self, product_id: int, data: SkuCreate) -> SkuResponse | None:
        """为指定商品创建SKU"""
        product = await self.db.get(Product, product_id)
        if product is None:
            return None

        sku = Sku(
            product_id=product_id,
            sku_code=data.sku_code,
            price=data.price,
            stock=data.stock,
            attrs=data.attrs,
            image_url=data.image_url,
        )
        self.db.add(sku)
        try:
            await self.db.flush()
        except sa_exc.IntegrityError as e:
            raise DatabaseException(
                message="SKU编码重复",
                detail=str(e),
                original_exception=e,
            ) from e
        await self.db.refresh(sku)
        return SkuResponse.model_validate(sku)

    async def get_sku(self, sku_id: int) -> SkuResponse | None:
        """根据ID获取SKU详情"""
        stmt = select(Sku).where(Sku.id == sku_id)
        result = await self.db.execute(stmt)
        sku = result.scalar_one_or_none()
        if sku is None:
            return None
        return SkuResponse.model_validate(sku)

    async def list_skus(self, product_id: int) -> list[SkuResponse]:
        """获取指定商品下的所有SKU"""
        stmt = select(Sku).where(Sku.product_id == product_id)
        result = await self.db.execute(stmt)
        return [SkuResponse.model_validate(s) for s in result.scalars().all()]

    async def update_sku(self, sku_id: int, data: SkuUpdate) -> SkuResponse | None:
        """更新SKU信息，仅更新传入的字段。

        用 UPDATE ... RETURNING 单条语句完成更新并拿回最新行，
        避免「先查后改再刷」的多次往返，缩短事务。
        """
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_sku(sku_id)

        stmt = update(Sku).where(Sku.id == sku_id).values(**update_data).returning(Sku)
        try:
            result = await self.db.execute(stmt)
            sku = result.scalar_one_or_none()
        except sa_exc.IntegrityError as e:
            raise DatabaseException(
                message="SKU编码重复",
                detail=str(e),
                original_exception=e,
            ) from e

        if sku is None:
            return None
        return SkuResponse.model_validate(sku)

    async def delete_sku(self, sku_id: int) -> bool:
        """删除SKU，单条 DELETE 完成，无需先查询。"""
        result = await self.db.execute(
            delete(Sku).where(Sku.id == sku_id).returning(Sku.id)
        )
        return result.scalar_one_or_none() is not None

    async def update_stock(self, sku_id: int, quantity: int) -> SkuResponse | None:
        """设置SKU库存为指定数量，单条 UPDATE 完成。"""
        result = await self.db.execute(
            update(Sku).where(Sku.id == sku_id).values(stock=quantity).returning(Sku)
        )
        sku = result.scalar_one_or_none()
        if sku is None:
            return None
        return SkuResponse.model_validate(sku)
