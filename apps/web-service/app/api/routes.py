from fastapi import APIRouter

from app.api import (
    categories,
    items,
    products,
    settings,
    skus,
    upload,
    welcome,
    auth,
    ai,
    ai_sse,
    ai_ws,
)

api_router = APIRouter()
api_router.include_router(welcome.router)
api_router.include_router(items.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(skus.router)
api_router.include_router(settings.router)
api_router.include_router(upload.router)
api_router.include_router(auth.router)
api_router.include_router(ai.router)
api_router.include_router(ai_sse.router)
api_router.include_router(ai_ws.router)
