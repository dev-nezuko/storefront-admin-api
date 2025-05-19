from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from app.db.base import Base

class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    reason = Column(String(255), default="manual update")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
