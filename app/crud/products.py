from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.products import Product
from app.schemas.products import ProductCreate

async def create_product(db: AsyncSession, product_in: ProductCreate) -> Product:
    new = Product(**product_in.dict())
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return new

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Product).offset(skip).limit(limit))
    return result.scalars().all()
