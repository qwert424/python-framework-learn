# 开发排障记录（学习用）

> 记录 2026-09-19 在本项目（uv workspace + FastAPI）遇到的两个问题、原因与解法。

## 1. `uv sync` 不会同步 workspace 里所有成员的依赖

### 现象

在 workspace 根目录执行 `uv sync`（或 `uv sync --all-groups`）后，`apps/web-service` 里声明的 `fastapi[standard]==0.136.3` 并没有被安装：

```text
uv pip show fastapi   # Package(s) not found for: fastapi
```

### 原因

本项目是一个 uv workspace（根 `pyproject.toml` 的 `[tool.uv.workspace]` 把 `apps/*`、`packages/*` 列为成员）：

- 根项目 `duyi-service` 的 `dependencies = []`
- `fastapi` 声明在成员 `web-service` 中

uv 0.6+ 起，`uv sync` 在 workspace 根目录**默认只同步根项目**，不会自动同步所有成员。

### 解法

```powershell
# 同步所有成员 + 所有依赖组
uv sync --all-packages --all-groups

# 只同步指定成员
uv sync --package web-service

# 运行指定成员的命令
uv run --package web-service fastapi dev apps/web-service/main.py --port 8080
```

关键参数：

- `--all-packages`：同步 workspace 全部成员
- `--package <name>`：只同步某个成员
- `--all-groups`：包含所有 dependency groups（与成员维度无关）

## 2. FastAPI 的 `/docs` 打不开（`SwaggerUIBundle is not defined`）

### 现象

浏览器打开 `http://127.0.0.1:8080/docs` 时控制台报错：

```text
Failed to load resource: net::ERR_CONNECTION_RESET   swagger-ui-bundle.js
Uncaught ReferenceError: SwaggerUIBundle is not defined
```

### 原因

FastAPI 默认从 CDN 加载 Swagger UI 静态资源：

- JS: `https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js`
- CSS: `https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css`

国内网络访问 jsdelivr 经常被重置（`ERR_CONNECTION_RESET`），JS 加载失败后 `SwaggerUIBundle` 未定义。

### 解法：本地化静态资源

1. 下载资源到 `apps/web-service/static/swagger/`：

```powershell
New-Item -ItemType Directory -Force -Path "apps/web-service/static/swagger" | Out-Null
curl.exe -sL -o "apps/web-service/static/swagger/swagger-ui-bundle.js" "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"
curl.exe -sL -o "apps/web-service/static/swagger/swagger-ui.css" "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
curl.exe -sL -o "apps/web-service/static/swagger/favicon.png" "https://fastapi.tiangolo.com/img/favicon.png"
```

2. 修改 `apps/web-service/main.py`，把 CDN 地址改为本地静态路径，并挂载静态目录：

```python
from pathlib import Path

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    swagger_js_url="/static/swagger/swagger-ui-bundle.js",
    swagger_css_url="/static/swagger/swagger-ui.css",
    swagger_favicon_url="/static/swagger/favicon.png",
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
```

> 注意：`BASE_DIR` 用 `__file__` 定位，避免因启动时的工作目录（如 workspace 根目录）不同而找不到 `static/`。

### 验证

```text
GET /docs                                     # 页面引用本地资源，可正常打开
GET /static/swagger/swagger-ui-bundle.js       # 200
GET /static/swagger/swagger-ui.css             # 200
GET /openapi.json                              # 200
```
