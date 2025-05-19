from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.products import Product
from app.schemas.products import ProductCreate


class DuplicateProductName(Exception):
    pass


async def create_product(db: AsyncSession, product_in: ProductCreate) -> Product:
    new = Product(**product_in.model_dump())
    db.add(new)
    try:
        await db.commit()
    except IntegrityError as exc:
        # name is the only unique column, so this is a duplicate name.
        await db.rollback()
        raise DuplicateProductName(product_in.name) from exc
    await db.refresh(new)
    return new

async def product_exists(db: AsyncSession, product_id: int) -> bool:
    return await db.get(Product, product_id) is not None

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Product).offset(skip).limit(limit))
    return result.scalars().all()
