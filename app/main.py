from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routers import products, sales, inventory
from app.db.base import Base
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # You could add shutdown logic after `yield`

app = FastAPI(lifespan=lifespan)

app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(sales.router)
