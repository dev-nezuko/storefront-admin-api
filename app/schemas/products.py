from pydantic import BaseModel
from decimal import Decimal

class ProductBase(BaseModel):
    name: str
    category: str
    price: Decimal
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int

    class Config:
        orm_mode = True
