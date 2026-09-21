from fastapi import APIRouter

from app.api import categories, items, products, settings, skus, upload, welcome, auth

api_router = APIRouter()
api_router.include_router(welcome.router)
api_router.include_router(items.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(skus.router)
api_router.include_router(settings.router)
api_router.include_router(upload.router)
api_router.include_router(auth.router)
