from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryLogRead(BaseModel):
    id: int
    product_id: int = Field(gt=0)
    quantity_change: int
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
