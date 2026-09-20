"""SKU 接口集成测试"""

from httpx import AsyncClient

PRODUCTS_URL = "/api/products"


async def _create_product(client: AsyncClient, name: str = "测试商品") -> dict:
    resp = await client.post(PRODUCTS_URL, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["data"]


def _sku_url(product_id: int) -> str:
    return f"/api/products/{product_id}/skus"


def _sku_detail_url(sku_id: int) -> str:
    return f"/api/skus/{sku_id}"


def _payload(sku_code: str, **kwargs) -> dict:
    data = {
        "sku_code": sku_code,
        "price": "99.99",
        "stock": 100,
        "attrs": {"颜色": "黑色"},
        "image_url": "/images/test.jpg",
    }
    data.update(kwargs)
    return data


class TestCreateSku:
    async def test_create_ok(self, async_client: AsyncClient):
        product = await _create_product(async_client)

        resp = await async_client.post(_sku_url(product["id"]), json=_payload("SKU-001"))
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["sku_code"] == "SKU-001"
        assert data["product_id"] == product["id"]

    async def test_create_product_not_found(self, async_client: AsyncClient):
        resp = await async_client.post(_sku_url(99999), json=_payload("SKU-002"))
        assert resp.status_code == 404
        assert resp.json()["code"] == "404001"

    async def test_create_duplicate_sku_code(self, async_client: AsyncClient):
        product = await _create_product(async_client)
        payload = _payload("SKU-DUP")

        await async_client.post(_sku_url(product["id"]), json=payload)
        resp = await async_client.post(_sku_url(product["id"]), json=payload)
        assert resp.status_code == 409
        assert resp.json()["code"] == "409001"


class TestGetSku:
    async def test_get_not_found(self, async_client: AsyncClient):
        resp = await async_client.get(_sku_detail_url(99999))
        assert resp.status_code == 404
        assert resp.json()["code"] == "404001"


class TestUpdateStock:
    async def test_update_stock_ok(self, async_client: AsyncClient):
        product = await _create_product(async_client)
        created = await async_client.post(_sku_url(product["id"]), json=_payload("SKU-S"))
        sku_id = created.json()["data"]["id"]

        resp = await async_client.patch(
            f"/api/skus/{sku_id}/stock", params={"stock": 50}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["stock"] == 50
