from fastapi import APIRouter

from app.api import categories, items, products, skus, welcome

api_router = APIRouter()
api_router.include_router(welcome.router)
api_router.include_router(items.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(skus.router)
