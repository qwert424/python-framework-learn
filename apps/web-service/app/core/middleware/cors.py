from starlette.middleware.cors import CORSMiddleware

from app.core.config import web_settings


def _split_csv(value: str) -> list[str]:
    """把逗号分隔的配置字符串拆成去空、去首尾空格的列表。"""
    return [item.strip() for item in value.split(",") if item.strip()]


origins = _split_csv(web_settings.cors_origins)
expose_headers = _split_csv(web_settings.cors_expose_headers)

MIDDLEWARE: tuple[object, dict[str, object]] = (
    CORSMiddleware,
    {
        "allow_origins": origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "expose_headers": expose_headers,
    },
)
