"""Run the API against real MySQL tables created from schema.sql.

Skipped unless TEST_MYSQL_URL points at a disposable database: every test
drops and recreates the tables. The compose `tests` service points it at
the throwaway `test-db` service.
"""

import os
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import app

MYSQL_URL = os.environ.get("TEST_MYSQL_URL")
SCHEMA_SQL = Path(__file__).resolve().parent.parent / "schema.sql"

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(not MYSQL_URL, reason="TEST_MYSQL_URL is not set"),
]


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(MYSQL_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        for statement in SCHEMA_SQL.read_text().split(";"):
            if statement.strip():
                await conn.execute(text(statement))
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def mysql_session():
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = mysql_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()
    await engine.dispose()


async def make_product(client, name="Desk lamp", category="Lighting", price="30.00"):
    response = await client.post("/products/", json={"name": name, "category": category, "price": price})
    assert response.status_code == 201
    return response.json()


async def test_round_trip_keeps_money_exact(client):
    product = await make_product(client, price="12.50")
    assert product["price"] == "12.50"
    for amount in ("0.10", "0.20", "0.10"):
        sale = {"product_id": product["id"], "quantity_sold": 1, "sale_date": "2025-03-04", "total_amount": amount}
        assert (await client.post("/sales/", json=sale)).status_code == 201
    assert (await client.get("/sales/summary?interval=day")).json() == [{"period": "2025-03-04", "revenue": "0.40"}]
    assert (await client.get("/sales/summary_by_category")).json() == [{"category": "Lighting", "revenue": "0.40"}]


async def test_summaries_group_mysql_dates(client):
    product = await make_product(client)
    for day, amount in (("2024-12-31", "10.00"), ("2025-01-02", "5.00"), ("2025-01-06", "1.00")):
        sale = {"product_id": product["id"], "quantity_sold": 1, "sale_date": day, "total_amount": amount}
        await client.post("/sales/", json=sale)
    weeks = (await client.get("/sales/summary?interval=week")).json()
    months = (await client.get("/sales/summary?interval=month")).json()
    assert weeks == [{"period": "2025-W01", "revenue": "15.00"}, {"period": "2025-W02", "revenue": "1.00"}]
    assert months == [{"period": "2024-12", "revenue": "10.00"}, {"period": "2025-01", "revenue": "6.00"}]


async def test_foreign_key_and_unique_violations_are_client_errors(client):
    await make_product(client)
    duplicate = await client.post("/products/", json={"name": "Desk lamp", "category": "Lighting", "price": "1.00"})
    assert duplicate.status_code == 409
    sale = {"product_id": 999, "quantity_sold": 1, "sale_date": "2025-01-01", "total_amount": "1.00"}
    assert (await client.post("/sales/", json=sale)).status_code == 404
    assert (await client.post("/inventory/", json={"product_id": 999, "quantity": 1})).status_code == 404


async def test_inventory_entry_writes_a_log(client):
    product = await make_product(client)
    created = await client.post("/inventory/", json={"product_id": product["id"], "quantity": 4})
    assert created.status_code == 201
    logs = (await client.get(f"/inventory/logs/{product['id']}")).json()
    assert [(log["quantity_change"], log["reason"]) for log in logs] == [(4, "initial stock")]
