from pydantic import BaseModel
from datetime import datetime

class InventoryLogRead(BaseModel):
    id: int
    product_id: int
    quantity_change: int
    reason: str
    created_at: datetime

    class Config:
        orm_mode = True
