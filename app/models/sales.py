from sqlalchemy import Column, Integer, ForeignKey, Date, Numeric
from app.db.base import Base

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    sale_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
