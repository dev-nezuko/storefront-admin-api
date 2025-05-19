import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_sale():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/sales/", json={
            "product_id": 1,
            "quantity_sold": 3,
            "sale_date": "2025-05-19",
            "total_amount": 59.97
        })
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == 1

@pytest.mark.asyncio
async def test_list_sales():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/sales/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_sales_summary():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/sales/summary?interval=month")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_sales_summary_by_category():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/sales/summary_by_category")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_sales_compare():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/sales/compare?interval=month")
        assert response.status_code == 200
        assert "current_period_revenue" in response.json()
