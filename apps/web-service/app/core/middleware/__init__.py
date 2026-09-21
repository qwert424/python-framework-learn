import inspect
from typing import Any, cast

from fastapi import FastAPI

from app.core.middleware import cors, process_time, response, logging

MIDDLEWARES = [
    process_time.MIDDLEWARE,
    cors.MIDDLEWARE,
    response.MIDDLEWARE,
    logging.MIDDLEWARE,
]


def register_middleware(app: FastAPI) -> None:
    for callable_obj, kwargs in MIDDLEWARES:
        if inspect.isclass(callable_obj):
            app.add_middleware(cast(Any, callable_obj), **kwargs)  # type: ignore[arg-type]

        else:
            app.middleware("http")(callable_obj, **kwargs)  # type: ignore[type-var]
