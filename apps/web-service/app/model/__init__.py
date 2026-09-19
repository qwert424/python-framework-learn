"""模型包：导入本包即自动注册所有 ORM 模型到 Base.metadata。"""

from app.model.base import Base, IDMixin, TimestampMixin
from app.model.category import Category
from app.model.product import Product
from app.model.sku import Sku

__all__ = [
    "Base",
    "IDMixin",
    "TimestampMixin",
    "Category",
    "Product",
    "Sku",
]
