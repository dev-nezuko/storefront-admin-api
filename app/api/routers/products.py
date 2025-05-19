from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.crud.products import create_product, get_products
from app.schemas.products import ProductCreate, ProductRead
from app.db.session import get_db

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def register_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_product(db, product_in)

@router.get("/", response_model=List[ProductRead])
async def list_products(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await get_products(db, skip=skip, limit=limit)
