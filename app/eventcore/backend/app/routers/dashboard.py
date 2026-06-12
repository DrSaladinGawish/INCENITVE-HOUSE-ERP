from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.surgery_deps import (
    generate_invoice_pdf,
    get_current_user,
    get_redis,
    log_audit_entry,
    require_permission,
    validate_date_range,
)
from app.database import get_db
from app.models.job import Job
from app.models.purchase_invoice import PurchaseInvoice
from app.models.bank_transaction import BankTransaction

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_db)):
    total_jobs = await db.scalar(
        select(func.count(Job.id))
    ) or 0

    active_jobs = await db.scalar(
        select(func.count(Job.id)).where(Job.status == "active")
    ) or 0

    completed_q = await db.scalar(
        select(func.count(Job.id)).where(Job.status == "completed")
    ) or 0

    pending_approval = await db.scalar(
        select(func.count(Job.id)).where(Job.status == "pending_approval")
    ) or 0

    revenue = await db.scalar(
        select(func.coalesce(func.sum(Job.total_revenue), 0))
    ) or 0

    cost = await db.scalar(
        select(func.coalesce(func.sum(Job.total_cost), 0))
    ) or 0

    avg_margin = await db.scalar(
        select(func.coalesce(func.avg(Job.margin_pct), 0))
    ) or 0

    unlinked = await db.scalar(
        select(func.count(PurchaseInvoice.id)).where(
            PurchaseInvoice.job_id.is_(None)
        )
    ) or 0

    unreconciled = await db.scalar(
        select(func.count(BankTransaction.id)).where(
            BankTransaction.is_reconciled == False
        )
    ) or 0

    now = datetime.now(timezone.utc).isoformat()

    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "completed_q": completed_q,
        "pending_approval": pending_approval,
        "revenue_q": float(revenue),
        "cost_q": float(cost),
        "on_time_pct": round(float(avg_margin), 1),
        "refreshed_at": now,
        "avg_margin_pct": round(float(avg_margin), 1),
        "unlinked_purchases": unlinked,
        "unreconciled_transactions": unreconciled,
        "cash_position": float(revenue) - float(cost),
    }


@router.get("/client-flipper")
async def get_client_flipper(db: AsyncSession = Depends(get_db)):
    from app.models.client import Client

    result = await db.execute(
        select(
            Client.id,
            Client.name,
            func.coalesce(func.sum(Job.total_revenue), 0).label("revenue"),
            func.coalesce(func.avg(Job.margin_pct), 0).label("margin"),
            func.count(Job.id).label("job_count"),
        )
        .join(Job, Job.client_id == Client.id, isouter=True)
        .group_by(Client.id, Client.name)
        .order_by(Client.name)
    )
    rows = result.all()
    return [
        {
            "client_id": str(r.id),
            "client_name": r.name,
            "total_revenue": float(r.revenue),
            "margin_pct": round(float(r.margin), 1),
            "job_count": r.job_count,
        }
        for r in rows
    ]


@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db)):
    alerts = []

    unlinked = await db.execute(
        select(PurchaseInvoice).where(PurchaseInvoice.job_id.is_(None)).limit(10)
    )
    for pi in unlinked.scalars().all():
        alerts.append({
            "id": str(pi.id),
            "type": "critical",
            "message": f"Purchase invoice {pi.invoice_number} ({pi.vendor_name}, {float(pi.total_amount):,.0f} EGP) has no job link",
            "entity_type": "purchase_invoice",
            "entity_id": str(pi.id),
            "action_url": f"/purchases/{pi.id}/link",
        })

    unreconciled = await db.execute(
        select(BankTransaction)
        .where(BankTransaction.is_reconciled == False)
        .limit(10)
    )
    for bt in unreconciled.scalars().all():
        alerts.append({
            "id": str(bt.id),
            "type": "warning",
            "message": f"Bank transaction {bt.description} ({float(bt.amount):,.0f} EGP) is unreconciled",
            "entity_type": "bank_transaction",
            "entity_id": str(bt.id),
            "action_url": "/bank/reconciliation",
        })

    return alerts


# ── Surgery v4.1: New dashboard endpoints ─────────────────────


@router.get("/kpi/snapshots")
async def get_kpi_snapshots(
    months: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
):
    """Return monthly KPI snapshots for line charts (revenue, cost, margin)."""
    _ = db  # placeholder
    # TODO: query monthly aggregated revenue / cost / margin from Job table
    return [
        {
            "month": "2025-10",
            "revenue": 420000,
            "cost": 310000,
            "margin_pct": 26.2,
        },
        {
            "month": "2025-11",
            "revenue": 385000,
            "cost": 298000,
            "margin_pct": 22.6,
        },
        {
            "month": "2025-12",
            "revenue": 510000,
            "cost": 372000,
            "margin_pct": 27.1,
        },
        {
            "month": "2026-01",
            "revenue": 465000,
            "cost": 341000,
            "margin_pct": 26.7,
        },
        {
            "month": "2026-02",
            "revenue": 398000,
            "cost": 315000,
            "margin_pct": 20.9,
        },
        {
            "month": "2026-03",
            "revenue": 532000,
            "cost": 389000,
            "margin_pct": 26.9,
        },
    ]


@router.get("/jobs/timeline")
async def get_jobs_timeline(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Return active jobs with start/end dates for Gantt-style bar chart."""
    _ = db
    _ = user
    # TODO: query jobs with status IN planning, executing, invoicing — return id, name,
    #       start_date, end_date, progress_pct
    return [
        {"job_id": "J001", "name": "Corporate Gala", "start": "2026-01-15", "end": "2026-03-20", "progress": 65},
        {"job_id": "J002", "name": "Product Launch", "start": "2026-02-01", "end": "2026-04-10", "progress": 40},
        {"job_id": "J003", "name": "Wedding Expo", "start": "2026-01-20", "end": "2026-02-28", "progress": 90},
        {"job_id": "J004", "name": "Conference Q2", "start": "2026-03-01", "end": "2026-05-15", "progress": 15},
        {"job_id": "J005", "name": "Award Ceremony", "start": "2026-02-10", "end": "2026-03-30", "progress": 55},
    ]


@router.get("/jobs/active")
async def get_active_jobs(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Return active job counts grouped by status (for donut chart)."""
    _ = db
    _ = user
    # TODO: SELECT status, COUNT(*) FROM job WHERE status IN (...) GROUP BY status
    return [
        {"status": "planning", "count": 12},
        {"status": "executing", "count": 8},
        {"status": "invoicing", "count": 5},
    ]


@router.get("/jobs/completed/qoq")
async def get_completed_jobs_qoq(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Return quarter-over-quarter completed job revenue and margin."""
    _ = db
    _ = user
    # TODO: group completed jobs by fiscal quarter, aggregate revenue & margin
    return [
        {"quarter": "2025 Q1", "revenue": 980000, "margin_pct": 24.5, "job_count": 18},
        {"quarter": "2025 Q2", "revenue": 1120000, "margin_pct": 26.1, "job_count": 22},
        {"quarter": "2025 Q3", "revenue": 1050000, "margin_pct": 25.3, "job_count": 20},
        {"quarter": "2025 Q4", "revenue": 1210000, "margin_pct": 27.8, "job_count": 25},
        {"quarter": "2026 Q1", "revenue": 1140000, "margin_pct": 26.5, "job_count": 23},
    ]


@router.get("/audit/log")
async def get_audit_log(
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Return recent audit log entries."""
    await require_permission(user, "audit:read")
    _ = db
    _ = limit
    # TODO: SELECT from audit_log table, ordered by timestamp DESC, limited
    return [
        {"timestamp": "2026-03-15T10:30:00", "user": "admin", "action": "invoice.generate", "entity": "INV-042"},
        {"timestamp": "2026-03-15T09:15:00", "user": "admin", "action": "job.update", "entity": "J005"},
        {"timestamp": "2026-03-14T16:45:00", "user": "sarah", "action": "quotation.create", "entity": "Q-023"},
        {"timestamp": "2026-03-14T14:20:00", "user": "admin", "action": "payment.reconcile", "entity": "BT-891"},
        {"timestamp": "2026-03-14T11:00:00", "user": "michael", "action": "vendor.create", "entity": "V-045"},
    ]


@router.post("/invoices/generate")
async def trigger_invoice_generate(
    invoice_id: str = Query(..., min_length=1),
    user: dict = Depends(get_current_user),
):
    """Generate a PDF for the given invoice and return download URL."""
    await require_permission(user, "invoice:generate")

    pdf_bytes = await generate_invoice_pdf(invoice_id)

    await log_audit_entry(
        user_id=user.get("user_id", ""),
        action="invoice.generate",
        entity_type="invoice",
        entity_id=invoice_id,
    )

    _ = pdf_bytes
    # TODO: save PDF to storage / return StreamingResponse
    return {
        "status": "generated",
        "invoice_id": invoice_id,
        "download_url": f"/api/v1/invoices/{invoice_id}/download",
    }


# ── Page routes for sidebar navigation ────────────────────────

PAGE_BASE = Path(__file__).resolve().parent.parent.parent.parent  # backend/ → project root
page_templates = Jinja2Templates(directory=str(PAGE_BASE / "templates"))


def _page(request: Request):
    return page_templates.TemplateResponse(request, "dashboard.html", {"request": request})


@router.get("/sales")
async def sales_page(request: Request):
    return _page(request)


@router.get("/purchase")
async def purchase_page(request: Request):
    return _page(request)


@router.get("/events")
async def events_page(request: Request):
    return _page(request)


@router.get("/operation")
async def operation_page(request: Request):
    return _page(request)


@router.get("/employees")
async def employees_page(request: Request):
    return _page(request)


@router.get("/accounts")
async def accounts_page(request: Request):
    return _page(request)


@router.get("/preferences")
async def preferences_page(request: Request):
    return _page(request)
