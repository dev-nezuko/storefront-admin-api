from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Literal
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.db.session import get_db
from app.crud import sales
from app.crud.products import product_exists
from app.schemas.sales import (
    CategoryRevenue,
    RevenueComparison,
    RevenuePeriod,
    SaleCreate,
    SaleRead,
)

CENT = Decimal("0.01")


def to_money(value) -> Decimal:
    # SQLite hands sums back as binary floats, so quantize before they reach JSON.
    return Decimal(str(value or 0)).quantize(CENT, rounding=ROUND_HALF_UP)


def check_date_range(start_date: Optional[date], end_date: Optional[date]) -> None:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")

router = APIRouter(prefix="/sales", tags=["Sales"])

# Create a new sale
@router.post("/", response_model=SaleRead, status_code=201)
async def create(sale: SaleCreate, db: AsyncSession = Depends(get_db)):
    if not await product_exists(db, sale.product_id):
        raise HTTPException(404, detail=f"Product {sale.product_id} not found")
    return await sales.create_sale(db, sale)

# List all or filtered sales
@router.get("/", response_model=List[SaleRead])
async def list_sales(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    product_id: Optional[int] = Query(None, gt=0),
    category: Optional[str] = Query(None, min_length=1, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    check_date_range(start_date, end_date)
    if not any([start_date, end_date, product_id, category]):
        return await sales.get_sales(db, skip, limit)

    return await sales.get_filtered_sales(
        db,
        start_date=start_date,
        end_date=end_date,
        product_id=product_id,
        category=category,
        skip=skip,
        limit=limit,
    )

# Revenue summary by interval
@router.get("/summary", response_model=List[RevenuePeriod])
async def revenue_summary(
    interval: Literal["day", "week", "month", "year"] = "month",
    db: AsyncSession = Depends(get_db)
):
    data = await sales.get_revenue_summary(db, interval)
    return [{"period": row[0], "revenue": to_money(row[1])} for row in data]

# Revenue summary by product category
@router.get("/summary_by_category", response_model=List[CategoryRevenue])
async def revenue_by_category(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    check_date_range(start_date, end_date)
    data = await sales.get_revenue_by_category(db, start_date, end_date)
    return [{"category": row[0], "revenue": to_money(row[1])} for row in data]

# Revenue comparison: current vs previous period
@router.get("/compare", response_model=RevenueComparison)
async def compare_revenue(
    interval: Literal["day", "week", "month", "year"] = "month",
    db: AsyncSession = Depends(get_db)
):
    current, previous = await sales.get_current_vs_previous_revenue(db, interval)
    current, previous = to_money(current), to_money(previous)
    change = None
    if previous > 0:
        change = ((current - previous) / previous * 100).quantize(CENT, rounding=ROUND_HALF_UP)
    return {
        "current_period_revenue": current,
        "previous_period_revenue": previous,
        "change_percent": change,
    }
