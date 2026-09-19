from fastapi import APIRouter

from app.schemas.item import Item

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/{item_id}")
def read_item(item_id: int, q: str | None = None) -> dict:
    return {"item_id": item_id, "q": q}


@router.put("/{item_id}")
def update_item(item_id: int, item: Item) -> dict:
    return {"item_name": item.name, "item_id": item_id}
