from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date
from fastapi.responses import JSONResponse

from app.db.session import get_db
from app.crud import sales
from app.schemas.sales import SaleCreate, SaleRead

router = APIRouter(prefix="/sales", tags=["Sales"])

# Create a new sale
@router.post("/", response_model=SaleRead)
async def create(sale: SaleCreate, db: AsyncSession = Depends(get_db)):
    return await sales.create_sale(db, sale)

# List all or filtered sales
@router.get("/", response_model=List[SaleRead])
async def list_sales(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    product_id: Optional[int] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
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
@router.get("/summary")
async def revenue_summary(
    interval: str = Query("month", enum=["day", "week", "month", "year"]),
    db: AsyncSession = Depends(get_db)
):
    try:
        data = await sales.get_revenue_summary(db, interval)
        return [{"period": row[0], "revenue": float(row[1])} for row in data]
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid interval"})

# Revenue summary by product category
@router.get("/summary_by_category")
async def revenue_by_category(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    data = await sales.get_revenue_by_category(db, start_date, end_date)
    return [{"category": row[0], "revenue": float(row[1])} for row in data]

# Revenue comparison: current vs previous period
@router.get("/compare")
async def compare_revenue(
    interval: str = Query("month", enum=["day", "week", "month", "year"]),
    db: AsyncSession = Depends(get_db)
):
    try:
        current, previous = await sales.get_current_vs_previous_revenue(db, interval)
        delta = (current - previous) / previous * 100 if previous > 0 else 0
        return {
            "current_period_revenue": float(current),
            "previous_period_revenue": float(previous),
            "change_percent": round(delta, 2)
        }
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid interval"})
