"""分类接口集成测试"""

from httpx import AsyncClient

CATEGORIES_URL = "/api/categories"


async def _create(client: AsyncClient, name: str, description: str = "") -> dict:
    resp = await client.post(
        CATEGORIES_URL, json={"name": name, "description": description}
    )
    assert resp.status_code == 201
    return resp.json()["data"]


class TestCreateCategory:
    async def test_create_ok(self, async_client: AsyncClient):
        resp = await async_client.post(CATEGORIES_URL, json={"name": "电子"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["code"] == "0"
        assert body["data"]["name"] == "电子"
        assert body["data"]["description"] == ""

    async def test_create_missing_name(self, async_client: AsyncClient):
        resp = await async_client.post(CATEGORIES_URL, json={})
        assert resp.status_code == 422
        assert resp.json()["code"] == "422001"


class TestListCategories:
    async def test_list_empty(self, async_client: AsyncClient):
        resp = await async_client.get(CATEGORIES_URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_with_data(self, async_client: AsyncClient):
        await _create(async_client, "分类A")
        await _create(async_client, "分类B")

        resp = await async_client.get(CATEGORIES_URL)
        data = resp.json()["data"]
        assert data["total"] == 2
        assert len(data["items"]) == 2


class TestGetCategory:
    async def test_get_found(self, async_client: AsyncClient):
        created = await _create(async_client, "服装")

        resp = await async_client.get(f"{CATEGORIES_URL}/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "服装"

    async def test_get_not_found(self, async_client: AsyncClient):
        resp = await async_client.get(f"{CATEGORIES_URL}/99999")
        assert resp.status_code == 404
        assert resp.json()["code"] == "404001"


class TestUpdateCategory:
    async def test_update_ok(self, async_client: AsyncClient):
        created = await _create(async_client, "旧名")

        resp = await async_client.put(
            f"{CATEGORIES_URL}/{created['id']}", json={"name": "新名"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "新名"

    async def test_update_not_found(self, async_client: AsyncClient):
        resp = await async_client.put(f"{CATEGORIES_URL}/99999", json={"name": "x"})
        assert resp.status_code == 404


class TestDeleteCategory:
    async def test_delete_ok(self, async_client: AsyncClient):
        created = await _create(async_client, "待删")

        resp = await async_client.delete(f"{CATEGORIES_URL}/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["code"] == "0"

        resp = await async_client.get(f"{CATEGORIES_URL}/{created['id']}")
        assert resp.status_code == 404

    async def test_delete_not_found(self, async_client: AsyncClient):
        resp = await async_client.delete(f"{CATEGORIES_URL}/99999")
        assert resp.status_code == 404
