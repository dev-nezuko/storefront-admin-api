from datetime import date
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from app.crud.sales import period_bounds, period_label
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


@pytest.mark.parametrize(
    ("interval", "today", "expected"),
    [
        ("day", date(2025, 3, 1), (date(2025, 3, 1), date(2025, 2, 28), date(2025, 2, 28))),
        ("week", date(2025, 1, 1), (date(2024, 12, 30), date(2024, 12, 23), date(2024, 12, 29))),
        ("month", date(2024, 3, 31), (date(2024, 3, 1), date(2024, 2, 1), date(2024, 2, 29))),
        ("month", date(2025, 1, 15), (date(2025, 1, 1), date(2024, 12, 1), date(2024, 12, 31))),
        ("year", date(2025, 1, 1), (date(2025, 1, 1), date(2024, 1, 1), date(2024, 12, 31))),
    ],
)
def test_period_bounds(interval, today, expected):
    assert period_bounds(interval, today) == expected


def test_week_label_follows_iso_year_across_new_year():
    assert period_label(date(2024, 12, 30), "week") == "2025-W01"
    assert period_label(date(2025, 1, 5), "week") == "2025-W01"
    assert period_label(date(2025, 1, 6), "week") == "2025-W02"


@pytest.mark.asyncio
async def test_weekly_summary_keeps_new_year_week_together():
    await add_sales((date(2024, 12, 31), "10.00"), (date(2025, 1, 2), "5.00"), (date(2025, 1, 6), "1.00"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        body = (await client.get("/sales/summary?interval=week")).json()
    assert body == [{"period": "2025-W01", "revenue": "15.00"}, {"period": "2025-W02", "revenue": "1.00"}]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("interval", "periods"),
    [("day", ["2024-12-31", "2025-01-02"]), ("month", ["2024-12", "2025-01"]), ("year", ["2024", "2025"])],
)
async def test_summary_periods_are_strings(interval, periods):
    await add_sales((date(2024, 12, 31), "10.00"), (date(2025, 1, 2), "5.00"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        body = (await client.get(f"/sales/summary?interval={interval}")).json()
    assert [row["period"] for row in body] == periods


@pytest.mark.asyncio
async def test_date_filters_are_inclusive():
    await add_sales((date(2025, 1, 1), "1.00"), (date(2025, 1, 31), "2.00"), (date(2025, 2, 1), "4.00"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        listed = (await client.get("/sales/?start_date=2025-01-01&end_date=2025-01-31")).json()
        by_category = (await client.get("/sales/summary_by_category?start_date=2025-01-01&end_date=2025-01-31")).json()
    assert sorted(row["total_amount"] for row in listed) == ["1.00", "2.00"]
    assert by_category == [{"category": "Demo", "revenue": "3.00"}]


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/sales/", "/sales/summary_by_category"])
async def test_reversed_date_range_is_rejected(path):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"{path}?start_date=2025-02-01&end_date=2025-01-01")
    assert response.status_code == 422
