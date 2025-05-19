import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_product():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/products/", json={
            "name": "Test Product",
            "category": "Test Category",
            "price": 19.99,
            "is_active": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Product"

@pytest.mark.asyncio
async def test_list_products():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/products/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
