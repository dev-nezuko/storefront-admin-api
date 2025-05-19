import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["CREATE_SCHEMA"] = "false"
import pytest_asyncio
from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.models.products import Product

@pytest_asyncio.fixture(autouse=True)
async def isolated_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        session.add(Product(id=1, name="Synthetic fixture", category="Demo", price=10, is_active=True))
        await session.commit()
    yield
    await engine.dispose()
