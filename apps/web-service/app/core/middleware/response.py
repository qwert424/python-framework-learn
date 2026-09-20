import json

from fastapi import Request
from fastapi.responses import JSONResponse


async def unified_response(request: Request, call_next):
    response = await call_next(request)

    if not request.url.path.startswith("/api/"):
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    headers = dict(response.headers)
    headers.pop("content-length", None)

    if response.status_code >= 400:
        err = json.loads(body) if body else {}
        return JSONResponse(
            content={
                "code": err.get("code", str(response.status_code)),
                "data": None,
                "message": err.get("message", ""),
            },
            status_code=response.status_code,
            headers=headers,
        )

    data = json.loads(body) if body else None

    return JSONResponse(
        content={"code": "0", "data": data, "message": "success"},
        status_code=response.status_code,
        headers=headers,
    )


MIDDLEWARE = (unified_response, {})
