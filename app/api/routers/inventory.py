from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.crud import inventory
from app.schemas.inventory import InventoryCreate, InventoryRead
from app.schemas.inventory_log import InventoryLogRead
from app.crud.inventory import get_inventory_logs

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.post("/", response_model=InventoryRead)
async def create(inv: InventoryCreate, db: AsyncSession = Depends(get_db)):
    return await inventory.create_inventory(db, inv)

@router.get("/", response_model=List[InventoryRead])
async def list(
    skip: int = 0,
    limit: int = 100,
    low_stock: bool = False,
    threshold: int = 10,
    db: AsyncSession = Depends(get_db)
):
    if low_stock:
        return await inventory.get_low_stock_inventory(db, threshold=threshold, skip=skip, limit=limit)
    return await inventory.get_inventory(db, skip, limit)

@router.get("/logs/{product_id}", response_model=List[InventoryLogRead])
async def logs(product_id: int, db: AsyncSession = Depends(get_db)):
    return await get_inventory_logs(db, product_id)
