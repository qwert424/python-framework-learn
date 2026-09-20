from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 应用根目录：apps/web-service（config.py 位于 app/core/ 下，向上两级）
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class _BaseSettingsWithEnv(BaseSettings):
    """配置基类：统一从应用目录的 .env 读取，并忽略不认识的键。"""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


class CommonSettings(_BaseSettingsWithEnv):
    """全局通用配置。"""

    environment: str = "development"


class WebSettings(_BaseSettingsWithEnv):
    """Web 服务配置，环境变量以 WEB_ 为前缀。"""

    model_config = SettingsConfigDict(env_prefix="WEB_")

    app_name: str = "Web Service API"
    cors_origins: str = ""  # 实际读取 WEB_CORS_ORIGINS，多个来源用逗号分隔
    cors_expose_headers: str = ""  # 实际读取 WEB_CORS_EXPOSE_HEADERS


class DBSettings(_BaseSettingsWithEnv):
    """数据库配置，环境变量以 DB_ 为前缀。"""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = "127.0.0.1"
    port: int = 5432
    name: str = ""
    user: str = ""
    password: str = ""


common_settings = CommonSettings()
web_settings = WebSettings()
db_settings = DBSettings()
