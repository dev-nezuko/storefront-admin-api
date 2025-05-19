from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.sales import Sale
from app.schemas.sales import SaleCreate
from sqlalchemy import func
from app.models.products import Product
from sqlalchemy import and_, select, join, func
from datetime import date, timedelta
from decimal import Decimal



async def create_sale(db: AsyncSession, sale_in: SaleCreate):
    sale = Sale(**sale_in.model_dump())
    db.add(sale)
    await db.commit()
    await db.refresh(sale)
    return sale

async def get_sales(db: AsyncSession, skip=0, limit=100):
    result = await db.execute(select(Sale).order_by(Sale.id).offset(skip).limit(limit))
    return result.scalars().all()


def period_label(day: date, interval: str) -> str:
    if interval == "day":
        return day.isoformat()
    if interval == "week":
        iso_year, iso_week, _ = day.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if interval == "month":
        return f"{day.year}-{day.month:02d}"
    if interval == "year":
        return str(day.year)
    raise ValueError("Invalid interval")


async def get_revenue_summary(db: AsyncSession, interval: str = "month"):
    # Group per day in SQL and roll up here: ISO weeks stay intact across New
    # Year and the same code runs on MySQL and SQLite.
    result = await db.execute(
        select(Sale.sale_date, func.sum(Sale.total_amount))
        .group_by(Sale.sale_date)
        .order_by(Sale.sale_date)
    )
    totals: dict[str, Decimal] = {}
    for day, revenue in result.all():
        label = period_label(day, interval)
        totals[label] = totals.get(label, Decimal(0)) + Decimal(str(revenue))
    return list(totals.items())


async def get_filtered_sales(
    db: AsyncSession,
    start_date=None,
    end_date=None,
    product_id=None,
    category=None,
    skip=0,
    limit=100
):
    stmt = select(Sale).join(Product).order_by(Sale.id).offset(skip).limit(limit)

    filters = []
    if start_date:
        filters.append(Sale.sale_date >= start_date)
    if end_date:
        filters.append(Sale.sale_date <= end_date)
    if product_id:
        filters.append(Sale.product_id == product_id)
    if category:
        filters.append(Product.category == category)

    if filters:
        stmt = stmt.where(and_(*filters))

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_revenue_by_category(db: AsyncSession, start_date=None, end_date=None):
    stmt = select(Product.category, func.sum(Sale.total_amount)) \
        .join(Product) \
        .group_by(Product.category) \
        .order_by(Product.category)

    if start_date:
        stmt = stmt.where(Sale.sale_date >= start_date)
    if end_date:
        stmt = stmt.where(Sale.sale_date <= end_date)

    result = await db.execute(stmt)
    return result.all()



def period_bounds(interval: str, today: date):
    """Return (current_start, previous_start, previous_end); the current period runs to today."""
    if interval == "day":
        current_start = today
        previous_start = today - timedelta(days=1)
    elif interval == "week":
        current_start = today - timedelta(days=today.weekday())
        previous_start = current_start - timedelta(weeks=1)
    elif interval == "month":
        current_start = today.replace(day=1)
        previous_start = (current_start - timedelta(days=1)).replace(day=1)
    elif interval == "year":
        current_start = today.replace(month=1, day=1)
        previous_start = current_start.replace(year=current_start.year - 1)
    else:
        raise ValueError("Invalid interval")
    return current_start, previous_start, current_start - timedelta(days=1)


async def get_current_vs_previous_revenue(db: AsyncSession, interval: str = "month", today: date | None = None):
    today = today or date.today()
    current_start, previous_start, previous_end = period_bounds(interval, today)

    current_stmt = select(func.sum(Sale.total_amount)).where(Sale.sale_date >= current_start, Sale.sale_date <= today)
    previous_stmt = select(func.sum(Sale.total_amount)).where(
        Sale.sale_date >= previous_start, Sale.sale_date <= previous_end
    )

    current_result = await db.execute(current_stmt)
    previous_result = await db.execute(previous_stmt)

    current_total = current_result.scalar() or 0
    previous_total = previous_result.scalar() or 0

    return current_total, previous_total
