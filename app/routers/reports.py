import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract

from app.database import get_db
from app.models.models import EventDim, SalesInvoice, PurchaseInvoice, BankTransaction, ClientDim, VendorDim, EmployeeDim, EmployeeAssignment

router = APIRouter(tags=["reports"])


@router.get("/dashboard/kpi")
async def dashboard_kpis(db: AsyncSession = Depends(get_db)):
    rev = await db.execute(select(func.coalesce(func.sum(SalesInvoice.total_amount), 0)))
    cost = await db.execute(select(func.coalesce(func.sum(PurchaseInvoice.total_amount), 0)))
    active = await db.execute(select(func.count(EventDim.event_id)).where(EventDim.status == "active"))
    pending = await db.execute(select(func.count(SalesInvoice.inv_id)).where(SalesInvoice.status == "pending"))
    overdue = await db.execute(select(func.count(SalesInvoice.inv_id)).where(SalesInvoice.status.in_(["pending", "overdue"])).where(SalesInvoice.due_date < datetime.date.today()))
    bank = await db.execute(select(func.coalesce(func.sum(BankTransaction.balance), 0)))
    revenue = float(rev.scalar())
    cost_v = float(cost.scalar())
    return {
        "total_revenue": revenue,
        "total_cost": cost_v,
        "profit_margin": round(((revenue - cost_v) / revenue * 100), 2) if revenue else 0,
        "active_events": active.scalar() or 0,
        "pending_invoices": pending.scalar() or 0,
        "overdue_invoices": overdue.scalar() or 0,
        "bank_balance": float(bank.scalar()),
    }


@router.get("/monthly-trend")
async def monthly_trend(months: int = Query(12, le=36), db: AsyncSession = Depends(get_db)):
    rows = []
    today = datetime.date.today()
    for m in range(months):
        dt = today.replace(day=1) - datetime.timedelta(days=30 * m)
        label = dt.strftime("%Y-%m")
        rev = await db.execute(
            select(func.coalesce(func.sum(SalesInvoice.total_amount), 0))
            .where(extract("year", SalesInvoice.invoice_date) == dt.year)
            .where(extract("month", SalesInvoice.invoice_date) == dt.month)
        )
        cost = await db.execute(
            select(func.coalesce(func.sum(PurchaseInvoice.total_amount), 0))
            .where(extract("year", PurchaseInvoice.invoice_date) == dt.year)
            .where(extract("month", PurchaseInvoice.invoice_date) == dt.month)
        )
        r = float(rev.scalar())
        c = float(cost.scalar())
        rows.append({"month": label, "revenue": r, "cost": c, "profit": r - c})
    return rows


@router.get("/event-pnl")
async def event_pnl(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EventDim.event_code, EventDim.name, func.coalesce(EventDim.revenue, 0), func.coalesce(EventDim.actual_cost, 0))
    )
    rows = []
    for code, name, rev, cost in result.all():
        rev_f = float(rev)
        cost_f = float(cost)
        rows.append({
            "event_code": code, "event_name": name,
            "revenue": rev_f, "cost": cost_f, "profit": rev_f - cost_f,
            "margin": round(((rev_f - cost_f) / rev_f * 100), 2) if rev_f else 0,
        })
    return rows


@router.get("/top-clients")
async def top_clients(limit: int = Query(10, le=50), db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(ClientDim.name, func.coalesce(func.sum(SalesInvoice.total_amount), 0).label("total"))
        .join(SalesInvoice, SalesInvoice.client_id == ClientDim.client_id, isouter=True)
        .group_by(ClientDim.client_id)
        .order_by(func.sum(SalesInvoice.total_amount).desc())
        .limit(limit)
    )
    return [{"name": name, "total": float(tot)} for name, tot in r.all()]


@router.get("/top-vendors")
async def top_vendors(limit: int = Query(10, le=50), db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(VendorDim.name, func.coalesce(func.sum(PurchaseInvoice.total_amount), 0).label("total"))
        .join(PurchaseInvoice, PurchaseInvoice.vendor_id == VendorDim.vendor_id, isouter=True)
        .group_by(VendorDim.vendor_id)
        .order_by(func.sum(PurchaseInvoice.total_amount).desc())
        .limit(limit)
    )
    return [{"name": name, "total": float(tot)} for name, tot in r.all()]


@router.get("/balance-sheet")
async def balance_sheet(db: AsyncSession = Depends(get_db)):
    rev = await db.execute(select(func.coalesce(func.sum(SalesInvoice.total_amount), 0)))
    cost = await db.execute(select(func.coalesce(func.sum(PurchaseInvoice.total_amount), 0)))
    bank = await db.execute(select(func.coalesce(func.sum(BankTransaction.balance), 0)))
    return {
        "assets": {"bank_balance": float(bank.scalar()), "receivables": float(rev.scalar()) - float(cost.scalar())},
        "liabilities": {"payables": float(cost.scalar())},
        "equity": {"retained_earnings": float(rev.scalar()) - float(cost.scalar())},
    }


@router.get("/utilization")
async def utilization_report(db: AsyncSession = Depends(get_db)):
    emps = await db.execute(select(EmployeeDim).where(EmployeeDim.status == "active"))
    total = len(emps.scalars().all())
    assigned = await db.execute(select(func.count(func.distinct(EmployeeAssignment.employee_id))))
    return {"total_active_employees": total, "assigned_to_events": assigned.scalar() or 0, "utilization_pct": round((assigned.scalar() or 0) / total * 100, 2) if total else 0}


@router.get("/event-status-breakdown")
async def event_status_breakdown(db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(EventDim.status, func.count(EventDim.event_id))
        .group_by(EventDim.status)
    )
    return {status: cnt for status, cnt in r.all()}
