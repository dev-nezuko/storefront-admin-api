import pytest
from datetime import date, timedelta
from decimal import Decimal
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import AsyncSessionLocal
from app.models.sales import Sale

@pytest.mark.asyncio
async def test_negative_values_and_pagination_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for path in ["/products/?skip=-1", "/inventory/?limit=501", "/sales/?limit=0"]:
            assert (await client.get(path)).status_code == 422
        assert (await client.post("/inventory/",json={"product_id":1,"quantity":-1})).status_code == 422
        assert (await client.post("/sales/",json={"product_id":1,"quantity_sold":0,"sale_date":"2025-01-01","total_amount":5})).status_code == 422
        assert (await client.post("/products/",json={"name":"Example","category":"Demo","price":"NaN"})).status_code == 422

@pytest.mark.asyncio
async def test_comparison_excludes_future_sales():
    async with AsyncSessionLocal() as session:
        session.add_all([Sale(product_id=1,quantity_sold=1,sale_date=date.today(),total_amount=Decimal("10")),Sale(product_id=1,quantity_sold=1,sale_date=date.today()+timedelta(days=5),total_amount=Decimal("999"))])
        await session.commit()
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as client:
        response=await client.get("/sales/compare?interval=day")
        assert response.status_code==200
        assert response.json()["current_period_revenue"]==10

@pytest.mark.asyncio
async def test_revenue_category_and_recorded_sale_do_not_change_inventory():
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as client:
        await client.post("/inventory/",json={"product_id":1,"quantity":5})
        await client.post("/sales/",json={"product_id":1,"quantity_sold":2,"sale_date":"2025-01-01","total_amount":"20.00"})
        response=await client.get("/sales/summary_by_category")
        assert response.json()==[{"category":"Demo","revenue":20.0}]
        assert (await client.get("/inventory/")).json()[0]["quantity"]==5
