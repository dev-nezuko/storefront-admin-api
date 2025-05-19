import asyncio
import sys
from datetime import date, timedelta
from decimal import Decimal

from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.inventory import Inventory
from app.models.inventory_log import InventoryLog
from app.models.products import Product
from app.models.sales import Sale


async def seed(*, reset_demo=False):
    if not reset_demo:
        raise RuntimeError("Destructive demo reset requires explicit --reset-demo")

    async with engine.begin() as conn:
        # All models share Base.metadata, which orders drops/creates by foreign key.
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        products = [
            Product(name="Widget A", category="Gadgets", price=Decimal("19.99"), is_active=True),
            Product(name="Widget B", category="Gadgets", price=Decimal("29.99"), is_active=True),
            Product(name="Gizmo X", category="Tools", price=Decimal("9.99"), is_active=True),
            Product(name="Gizmo Y", category="Tools", price=Decimal("14.49"), is_active=False),
        ]
        session.add_all(products)
        await session.flush()

        inventory_data = [
            (products[0].id, 150),
            (products[1].id, 20),
            (products[2].id, 5),
            (products[3].id, 0),
        ]
        inventory = [
            Inventory(product_id=pid, quantity=qty) for pid, qty in inventory_data
        ]
        session.add_all(inventory)

        logs = [
            InventoryLog(
                product_id=pid,
                quantity_change=qty,
                reason="Initial Stock"
            )
            for pid, qty in inventory_data
        ]
        session.add_all(logs)

        sales = [
            Sale(product_id=products[0].id, quantity_sold=10, sale_date=date.today(), total_amount=Decimal("199.90")),
            Sale(product_id=products[0].id, quantity_sold=5, sale_date=date.today() - timedelta(days=1), total_amount=Decimal("99.95")),
            Sale(product_id=products[1].id, quantity_sold=2, sale_date=date.today(), total_amount=Decimal("59.98")),
            Sale(product_id=products[2].id, quantity_sold=1, sale_date=date.today() - timedelta(days=7), total_amount=Decimal("9.99")),
        ]
        session.add_all(sales)

        sale_logs = [
            InventoryLog(
                product_id=s.product_id,
                quantity_change=-s.quantity_sold,
                reason=f"Sale on {s.sale_date.isoformat()}"
            )
            for s in sales
        ]
        session.add_all(sale_logs)

        await session.commit()

async def main():
    try:
        await seed(reset_demo="--reset-demo" in sys.argv)
    finally:
        # Close pooled connections while the event loop is still running.
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
