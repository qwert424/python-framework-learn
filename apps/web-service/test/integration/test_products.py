"""商品接口集成测试"""

from httpx import AsyncClient

PRODUCTS_URL = "/api/products"
CATEGORIES_URL = "/api/categories"


async def _create_category(client: AsyncClient, name: str) -> dict:
    resp = await client.post(CATEGORIES_URL, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["data"]


async def _create_product(client: AsyncClient, **kwargs) -> dict:
    defaults = {"name": "测试商品"}
    defaults.update(kwargs)
    resp = await client.post(PRODUCTS_URL, json=defaults)
    assert resp.status_code == 201
    return resp.json()["data"]


class TestCreateProduct:
    async def test_create_ok(self, async_client: AsyncClient):
        resp = await async_client.post(PRODUCTS_URL, json={"name": "商品A"})
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "商品A"
        assert data["categories"] == []
        assert data["skus"] == []

    async def test_create_with_categories(self, async_client: AsyncClient):
        category = await _create_category(async_client, "分类1")

        resp = await async_client.post(
            PRODUCTS_URL, json={"name": "商品B", "category_ids": [category["id"]]}
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert len(data["categories"]) == 1
        assert data["categories"][0]["name"] == "分类1"

    async def test_create_missing_name(self, async_client: AsyncClient):
        resp = await async_client.post(PRODUCTS_URL, json={})
        assert resp.status_code == 422
        assert resp.json()["code"] == "422001"

    async def test_create_with_nonexistent_category(self, async_client: AsyncClient):
        resp = await async_client.post(
            PRODUCTS_URL, json={"name": "商品C", "category_ids": [99999]}
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "409001"


class TestListProducts:
    async def test_list_empty(self, async_client: AsyncClient):
        resp = await async_client.get(PRODUCTS_URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["items"] == []
        assert data["total"] == 0

    async def test_filter_by_keyword(self, async_client: AsyncClient):
        await _create_product(async_client, name="苹果手机")
        await _create_product(async_client, name="香蕉")

        resp = await async_client.get(PRODUCTS_URL, params={"keyword": "手机"})
        assert resp.json()["data"]["total"] == 1


class TestGetProduct:
    async def test_get_found(self, async_client: AsyncClient):
        product = await _create_product(async_client, name="商品X")

        resp = await async_client.get(f"{PRODUCTS_URL}/{product['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "商品X"

    async def test_get_not_found(self, async_client: AsyncClient):
        resp = await async_client.get(f"{PRODUCTS_URL}/99999")
        assert resp.status_code == 404
        assert resp.json()["code"] == "404001"


class TestDeleteProduct:
    async def test_delete_ok(self, async_client: AsyncClient):
        product = await _create_product(async_client, name="待删")

        resp = await async_client.delete(f"{PRODUCTS_URL}/{product['id']}")
        assert resp.status_code == 200

        resp = await async_client.get(f"{PRODUCTS_URL}/{product['id']}")
        assert resp.status_code == 404
