from datetime import date, datetime
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.inventory_log import InventoryLog
from app.models.products import Product
from app.models.sales import Sale


@pytest.mark.asyncio
async def test_pages_follow_insertion_order():
    async with AsyncSessionLocal() as session:
        session.add_all(Product(name=f"Item {n}", category="Demo", price=Decimal("1.00")) for n in range(2, 8))
        session.add_all(
            Sale(product_id=1, quantity_sold=1, sale_date=date(2025, 1, 1), total_amount=Decimal(n)) for n in range(1, 7)
        )
        await session.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        products = [(await client.get(f"/products/?skip={skip}&limit=3")).json() for skip in (0, 3)]
        sales = [(await client.get(f"/sales/?category=Demo&skip={skip}&limit=3")).json() for skip in (0, 3)]
    assert [p["id"] for page in products for p in page] == [1, 2, 3, 4, 5, 6]
    assert [s["id"] for page in sales for s in page] == [1, 2, 3, 4, 5, 6]


@pytest.mark.asyncio
async def test_logs_with_equal_timestamps_list_newest_id_first():
    async with AsyncSessionLocal() as session:
        stamp = datetime(2025, 1, 1, 12, 0, 0)
        session.add_all(InventoryLog(product_id=1, quantity_change=n, reason="count", created_at=stamp) for n in (1, 2, 3))
        await session.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logs = (await client.get("/inventory/logs/1")).json()
    assert [log["quantity_change"] for log in logs] == [3, 2, 1]
