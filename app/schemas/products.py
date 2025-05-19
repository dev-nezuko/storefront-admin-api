from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal

class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2, allow_inf_nan=False)
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
