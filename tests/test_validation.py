import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http


@pytest.mark.asyncio
async def test_sale_for_unknown_product_is_404(client):
    response = await client.post(
        "/sales/", json={"product_id": 99, "quantity_sold": 1, "sale_date": "2025-01-01", "total_amount": "1.00"}
    )
    assert response.status_code == 404
    assert (await client.get("/sales/")).json() == []


@pytest.mark.asyncio
async def test_inventory_for_unknown_product_is_404(client):
    response = await client.post("/inventory/", json={"product_id": 99, "quantity": 3})
    assert response.status_code == 404
    assert (await client.get("/inventory/")).json() == []


@pytest.mark.asyncio
async def test_logs_for_unknown_product_is_404(client):
    assert (await client.get("/inventory/logs/99")).status_code == 404
    assert (await client.get("/inventory/logs/0")).status_code == 422


@pytest.mark.asyncio
async def test_duplicate_product_name_is_409(client):
    response = await client.post("/products/", json={"name": "Synthetic fixture", "category": "Demo", "price": "1.00"})
    assert response.status_code == 409
    assert len((await client.get("/products/")).json()) == 1


@pytest.mark.asyncio
async def test_product_names_are_trimmed_and_blank_rejected(client):
    created = await client.post("/products/", json={"name": "  Desk lamp ", "category": " Lighting", "price": "30.00"})
    assert created.status_code == 201
    assert created.json()["name"] == "Desk lamp"
    assert created.json()["category"] == "Lighting"
    blank = await client.post("/products/", json={"name": "   ", "category": "Lighting", "price": "30.00"})
    assert blank.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("price", ["12.345", "-0.01", "100000000.00", "Infinity"])
async def test_price_outside_two_place_money_range_is_rejected(client, price):
    response = await client.post("/products/", json={"name": "Odd price", "category": "Demo", "price": price})
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["product_id=0", "category="])
async def test_invalid_sale_filters_are_rejected(client, query):
    assert (await client.get(f"/sales/?{query}")).status_code == 422
