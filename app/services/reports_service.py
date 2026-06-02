"""Financial and operational report service."""
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import EventDim, SalesInvoice, PurchaseInvoice, VendorDim, ClientDim, PNRDim, BankTransaction


async def monthly_trends(db: AsyncSession, months: int = 12) -> list:
    from sqlalchemy import extract
    rows = []
    today = datetime.date.today()
    for m in range(months):
        dt = today.replace(day=1) - datetime.timedelta(days=30 * m)
        label = dt.strftime("%Y-%m")
        rev = await db.execute(select(func.coalesce(func.sum(SalesInvoice.total_amount), 0)).where(extract("year", SalesInvoice.invoice_date) == dt.year).where(extract("month", SalesInvoice.invoice_date) == dt.month))
        cost = await db.execute(select(func.coalesce(func.sum(PurchaseInvoice.total_amount), 0)).where(extract("year", PurchaseInvoice.invoice_date) == dt.year).where(extract("month", PurchaseInvoice.invoice_date) == dt.month))
        rows.append({"month": label, "revenue": float(rev.scalar()), "cost": float(cost.scalar()), "profit": float(rev.scalar()) - float(cost.scalar())})
    return rows


async def top_clients(db: AsyncSession, limit: int = 10) -> list:
    r = await db.execute(
        select(ClientDim.name, func.coalesce(func.sum(SalesInvoice.total_amount), 0).label("total"))
        .join(SalesInvoice, SalesInvoice.client_id == ClientDim.client_id, isouter=True)
        .group_by(ClientDim.client_id)
        .order_by(func.sum(SalesInvoice.total_amount).desc())
        .limit(limit)
    )
    return [{"name": name, "total": float(tot)} for name, tot in r.all()]


async def top_vendors(db: AsyncSession, limit: int = 10) -> list:
    r = await db.execute(
        select(VendorDim.name, func.coalesce(func.sum(PurchaseInvoice.total_amount), 0).label("total"))
        .join(PurchaseInvoice, PurchaseInvoice.vendor_id == VendorDim.vendor_id, isouter=True)
        .group_by(VendorDim.vendor_id)
        .order_by(func.sum(PurchaseInvoice.total_amount).desc())
        .limit(limit)
    )
    return [{"name": name, "total": float(tot)} for name, tot in r.all()]
