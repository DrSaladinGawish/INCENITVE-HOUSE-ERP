"""Dashboard aggregation service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import EventDim, SalesInvoice, PurchaseInvoice, BankTransaction


async def get_kpi_data(db: AsyncSession) -> dict:
    rev = await db.execute(select(func.coalesce(func.sum(SalesInvoice.total_amount), 0)))
    cost = await db.execute(select(func.coalesce(func.sum(PurchaseInvoice.total_amount), 0)))
    active = await db.execute(select(func.count(EventDim.event_id)).where(EventDim.status == "active"))
    pending = await db.execute(select(func.count(SalesInvoice.inv_id)).where(SalesInvoice.status == "pending"))
    return {
        "total_revenue": float(rev.scalar()),
        "total_cost": float(cost.scalar()),
        "active_events": active.scalar(),
        "pending_invoices": pending.scalar(),
    }
