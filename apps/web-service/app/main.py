from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import common_settings, web_settings
from app.exception.handler import register_exception_handlers

is_production = common_settings.environment == "production"

app = FastAPI(
    title=web_settings.app_name,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)


# 注册全局异常处理器（覆盖 Starlette/FastAPI 内置处理器 + 兜底未知异常）
register_exception_handlers(app)
app.include_router(api_router)
