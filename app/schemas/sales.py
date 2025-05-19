from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from decimal import Decimal

class SaleBase(BaseModel):
    product_id: int = Field(gt=0)
    quantity_sold: int = Field(gt=0)
    sale_date: date
    total_amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2, allow_inf_nan=False)

class SaleCreate(SaleBase):
    pass

class SaleRead(SaleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
