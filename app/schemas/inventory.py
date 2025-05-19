from pydantic import BaseModel, ConfigDict, Field

class InventoryBase(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=0)

class InventoryCreate(InventoryBase):
    pass

class InventoryRead(InventoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
