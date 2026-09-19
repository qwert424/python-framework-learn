# from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

# from starlette.staticfiles import StaticFiles

# 根据环境变量决定
import os

is_production = os.getenv("ENVIRONMENT") == "production"

app = FastAPI(
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

# BASE_DIR = Path(__file__).resolve().parent

# # Swagger UI 资源改为本地静态文件，避免依赖被墙的 jsdelivr CDN
# app = FastAPI(
#     swagger_js_url="/static/swagger/swagger-ui-bundle.js",
#     swagger_css_url="/static/swagger/swagger-ui.css",
#     swagger_favicon_url="/static/swagger/favicon.png",
# )

# app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class Item(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}
