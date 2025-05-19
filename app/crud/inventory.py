from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.future import select
from app.models.inventory import Inventory
from app.schemas.inventory import InventoryCreate
from app.models.inventory_log import InventoryLog

async def create_inventory(db: AsyncSession, inventory_in: InventoryCreate):
    inv = Inventory(**inventory_in.dict())
    db.add(inv)
    await db.flush()

    log = InventoryLog(
        product_id=inv.product_id,
        quantity_change=inv.quantity,
        reason="initial stock"
    )
    db.add(log)
    await db.commit()
    await db.refresh(inv)
    return inv

async def get_inventory(db: AsyncSession, skip=0, limit=100):
    result = await db.execute(select(Inventory).offset(skip).limit(limit))
    return result.scalars().all()


async def get_low_stock_inventory(db: AsyncSession, threshold=10, skip=0, limit=100):
    result = await db.execute(
        select(Inventory).where(Inventory.quantity < threshold).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def get_inventory_logs(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(InventoryLog).where(InventoryLog.product_id == product_id).order_by(InventoryLog.created_at.desc())
    )
    return result.scalars().all()
