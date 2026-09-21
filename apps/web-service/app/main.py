from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import common_settings, web_settings
from app.core.middleware import register_middleware
from app.core.openapi import setup_openapi
from app.exception.handler import register_exception_handlers
from app.core.database import get_session_factory
from app.service.setting_service import SettingService


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with get_session_factory().begin() as session:
        await SettingService(session).initialize()
    yield


is_production = common_settings.environment == "production"

app = FastAPI(
    lifespan=lifespan,
    title=web_settings.app_name,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

# 注册中间件
register_middleware(app)

# 设置openapi的格式
setup_openapi(app)

# 注册全局异常处理器（覆盖 Starlette/FastAPI 内置处理器 + 兜底未知异常）
register_exception_handlers(app)
app.include_router(api_router)
