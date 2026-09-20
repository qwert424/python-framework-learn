"""业务逻辑层包：导出各 Service 类。"""

from app.service.base import BaseService, PageResult
from app.service.category_service import CategoryService
from app.service.product_service import ProductService
from app.service.sku_service import SkuService

__all__ = [
    "BaseService",
    "PageResult",
    "CategoryService",
    "ProductService",
    "SkuService",
]
