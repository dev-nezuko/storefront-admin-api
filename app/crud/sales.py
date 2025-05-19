from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.sales import Sale
from app.schemas.sales import SaleCreate
from sqlalchemy import func
from app.models.products import Product
from sqlalchemy import and_, select, join, func
from datetime import date, timedelta



async def create_sale(db: AsyncSession, sale_in: SaleCreate):
    sale = Sale(**sale_in.dict())
    db.add(sale)
    await db.commit()
    await db.refresh(sale)
    return sale

async def get_sales(db: AsyncSession, skip=0, limit=100):
    result = await db.execute(select(Sale).offset(skip).limit(limit))
    return result.scalars().all()


async def get_revenue_summary(db: AsyncSession, interval: str = "month"):
    group_expr = {
        "day": func.date(Sale.sale_date),
        "week": func.year(Sale.sale_date) * 100 + func.week(Sale.sale_date),
        "month": func.date_format(Sale.sale_date, "%Y-%m"),
        "year": func.year(Sale.sale_date),
    }.get(interval)

    if not group_expr:
        raise ValueError("Invalid interval")

    result = await db.execute(
        select(group_expr.label("period"), func.sum(Sale.total_amount).label("revenue"))
        .group_by(group_expr)
        .order_by(group_expr)
    )
    return result.all()




async def get_filtered_sales(
    db: AsyncSession,
    start_date=None,
    end_date=None,
    product_id=None,
    category=None,
    skip=0,
    limit=100
):
    stmt = select(Sale).join(Product).offset(skip).limit(limit)

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
        .group_by(Product.category)

    if start_date:
        stmt = stmt.where(Sale.sale_date >= start_date)
    if end_date:
        stmt = stmt.where(Sale.sale_date <= end_date)

    result = await db.execute(stmt)
    return result.all()



async def get_current_vs_previous_revenue(db: AsyncSession, interval: str = "month"):
    today = date.today()

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

    current_end = today
    previous_end = current_start - timedelta(days=1)

    current_stmt = select(func.sum(Sale.total_amount)).where(Sale.sale_date >= current_start)
    previous_stmt = select(func.sum(Sale.total_amount)).where(
        Sale.sale_date >= previous_start, Sale.sale_date <= previous_end
    )

    current_result = await db.execute(current_stmt)
    previous_result = await db.execute(previous_stmt)

    current_total = current_result.scalar() or 0
    previous_total = previous_result.scalar() or 0

    return current_total, previous_total
