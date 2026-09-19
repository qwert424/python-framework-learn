from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import common_settings, web_settings

is_production = common_settings.environment == "production"

app = FastAPI(
    title=web_settings.app_name,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.include_router(api_router)
