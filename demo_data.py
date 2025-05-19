import asyncio
from datetime import date, timedelta, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, engine
from app.models.products import Product
from app.models.inventory import Inventory
from app.models.sales import Sale
from app.models.inventory_log import InventoryLog
import sys

async def seed():

    async with engine.begin() as conn:
        await conn.run_sync(Product.metadata.drop_all)
        await conn.run_sync(Product.metadata.create_all)
        await conn.run_sync(Inventory.metadata.drop_all)
        await conn.run_sync(Inventory.metadata.create_all)
        await conn.run_sync(Sale.metadata.drop_all)
        await conn.run_sync(Sale.metadata.create_all)
        await conn.run_sync(InventoryLog.metadata.drop_all)
        await conn.run_sync(InventoryLog.metadata.create_all)

    async with AsyncSessionLocal() as session:

        products = [
            Product(name="Widget A", category="Gadgets", price=19.99, is_active=True),
            Product(name="Widget B", category="Gadgets", price=29.99, is_active=True),
            Product(name="Gizmo X", category="Tools", price=9.99, is_active=True),
            Product(name="Gizmo Y", category="Tools", price=14.49, is_active=False),
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
                reason="Initial Stock",
                created_at=datetime.utcnow()
            )
            for pid, qty in inventory_data
        ]
        session.add_all(logs)


        sales = [
            Sale(product_id=products[0].id, quantity_sold=10, sale_date=date.today(), total_amount=199.90),
            Sale(product_id=products[0].id, quantity_sold=5, sale_date=date.today() - timedelta(days=1), total_amount=99.95),
            Sale(product_id=products[1].id, quantity_sold=2, sale_date=date.today(), total_amount=59.98),
            Sale(product_id=products[2].id, quantity_sold=1, sale_date=date.today() - timedelta(days=7), total_amount=9.99),
        ]
        session.add_all(sales)


        sale_logs = [
            InventoryLog(
                product_id=s.product_id,
                quantity_change=-s.quantity_sold,
                reason=f"Sale on {s.sale_date.isoformat()}",
                created_at=datetime.utcnow()
            )
            for s in sales
        ]
        session.add_all(sale_logs)

        await session.commit()

if __name__ == "__main__":
    try:
        asyncio.run(seed())
    except RuntimeError as e:
        if "Event loop is closed" in str(e) and sys.version_info >= (3, 11):
            pass
