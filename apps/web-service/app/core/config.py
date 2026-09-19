from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """全局通用配置。"""

    # extra="ignore"：没有前缀的配置类会读到环境/`.env` 里的所有键，
    # 忽略不认识的键（如 WEB_APP_NAME），避免报 "Extra inputs are not permitted"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"


class WebSettings(BaseSettings):
    """Web 服务配置，环境变量统一以 WEB_ 为前缀。"""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="WEB_")

    app_name: str = "Web Service API"


common_settings = CommonSettings()
web_settings = WebSettings()
