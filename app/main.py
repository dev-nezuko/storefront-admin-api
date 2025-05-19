from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routers import products, sales, inventory
from app.db.base import Base
from app.core.config import settings
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.CREATE_SCHEMA:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await engine.dispose()

app = FastAPI(title="Storefront admin prototype", description="Local product, inventory and recorded-sale API. Authentication is not implemented.", lifespan=lifespan)

app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(sales.router)
