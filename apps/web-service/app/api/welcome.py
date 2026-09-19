from fastapi import APIRouter

router = APIRouter(tags=["welcome"])


@router.get("/", summary="Hello World", description="这是一个测试接口")
async def read_root() -> dict[str, str]:
    return {"Hello": "World"}
