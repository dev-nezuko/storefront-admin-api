from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.sales import Sale


async def add_sales(*rows):
    async with AsyncSessionLocal() as session:
        session.add_all(
            Sale(product_id=1, quantity_sold=1, sale_date=day, total_amount=Decimal(amount))
            for day, amount in rows
        )
        await session.commit()


@pytest.mark.asyncio
async def test_revenue_sums_are_exact_decimal_strings():
    today = date.today()
    await add_sales((today, "0.10"), (today, "0.20"), (today, "0.10"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        summary = (await client.get("/sales/summary?interval=day")).json()
        by_category = (await client.get("/sales/summary_by_category")).json()
    assert summary[0]["revenue"] == "0.40"
    assert by_category == [{"category": "Demo", "revenue": "0.40"}]


@pytest.mark.asyncio
async def test_change_percent_is_null_without_previous_revenue():
    await add_sales((date.today(), "25.00"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        body = (await client.get("/sales/compare?interval=day")).json()
    assert body == {
        "current_period_revenue": "25.00",
        "previous_period_revenue": "0.00",
        "change_percent": None,
    }


@pytest.mark.asyncio
async def test_change_percent_against_previous_day():
    today = date.today()
    await add_sales((today, "15.00"), (today - timedelta(days=1), "45.00"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        body = (await client.get("/sales/compare?interval=day")).json()
    assert body["previous_period_revenue"] == "45.00"
    assert body["change_percent"] == "-66.67"


@pytest.mark.asyncio
async def test_empty_period_reports_zero_revenue():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        body = (await client.get("/sales/compare?interval=month")).json()
    assert body["current_period_revenue"] == "0.00"
