from fastapi import APIRouter

from app.api import items, welcome

api_router = APIRouter()
api_router.include_router(welcome.router)
api_router.include_router(items.router)
