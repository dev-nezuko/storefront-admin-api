import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_inventory():
    async with AsyncClient(app=app, base_url="http://test") as client:

        response = await client.post("/inventory/", json={
            "product_id": 1,
            "quantity": 50
        })
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == 1

@pytest.mark.asyncio
async def test_list_inventory():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/inventory/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_low_stock_inventory():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/inventory/?low_stock=true&threshold=100")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
