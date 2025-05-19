from pydantic import BaseModel
from datetime import date
from decimal import Decimal

class SaleBase(BaseModel):
    product_id: int
    quantity_sold: int
    sale_date: date
    total_amount: Decimal

class SaleCreate(SaleBase):
    pass

class SaleRead(SaleBase):
    id: int

    class Config:
        orm_mode = True
