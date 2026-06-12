from uuid import UUID
from datetime import date, datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine
from app.models.purchase_invoice import PurchaseInvoice
from app.models.job import Job
from app.models.job_line_item import JobLineItem
from app.models.event import Event
from app.schemas.purchase_invoice import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceResponse,
    PurchaseInvoiceLinkRequest,
)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"
_page_templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

router = APIRouter(prefix="/api/v1/purchase-invoices", tags=["Purchase Invoices"])


@router.post("", response_model=PurchaseInvoiceResponse, status_code=201)
async def create_purchase_invoice(
    payload: PurchaseInvoiceCreate,
    db: AsyncSession = Depends(get_db),
):

    invoice = PurchaseInvoice(
        job_id=payload.job_id,
        event_id=payload.event_id,
        vendor_name=payload.vendor_name,
        vendor_id=payload.vendor_id,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        subtotal=payload.subtotal,
        vat_amount=payload.vat_amount,
        total_amount=payload.total_amount,
        currency=payload.currency,
        exchange_rate=payload.exchange_rate,
        linked_method="manual",
    )
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)
    return invoice


@router.get("", response_model=list[PurchaseInvoiceResponse])
async def list_purchase_invoices(
    job_id: UUID | None = Query(None),
    status: str | None = Query(None),
    unlinked: bool = Query(False),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(PurchaseInvoice).order_by(PurchaseInvoice.created_at.desc())
    if job_id:
        q = q.where(PurchaseInvoice.job_id == job_id)
    if status:
        q = q.where(PurchaseInvoice.status == status)
    if unlinked:
        q = q.where(PurchaseInvoice.job_id.is_(None))
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/unlinked", response_model=list[PurchaseInvoiceResponse])
async def get_unlinked_invoices(db: AsyncSession = Depends(get_db)):
    q = (
        select(PurchaseInvoice)
        .where(PurchaseInvoice.job_id.is_(None))
        .order_by(PurchaseInvoice.created_at.desc())
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/{invoice_id}/link", response_model=PurchaseInvoiceResponse)
async def link_purchase_invoice(
    invoice_id: UUID,
    payload: PurchaseInvoiceLinkRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PurchaseInvoice).where(PurchaseInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Purchase invoice not found")

    invoice.job_id = payload.job_id
    invoice.linked_method = payload.linked_method
    invoice.linked_at = _utcnow()
    await db.flush()

    # Create job line item for this cost
    item = JobLineItem(
        job_id=payload.job_id,
        type="cost",
        category=invoice.vendor_name,
        description=f"Purchase invoice {invoice.invoice_number}",
        total_amount=invoice.total_amount,
        source_type="purchase_invoice",
        source_id=invoice.id,
        is_committed=True,
    )
    db.add(item)
    await db.flush()

    # Recalculate job P&L
    rev = await db.scalar(
        select(func.coalesce(func.sum(JobLineItem.total_amount), 0)).where(
            JobLineItem.job_id == payload.job_id,
            JobLineItem.type == "revenue",
            JobLineItem.is_committed == True,
        )
    ) or 0
    cost = await db.scalar(
        select(func.coalesce(func.sum(JobLineItem.total_amount), 0)).where(
            JobLineItem.job_id == payload.job_id,
            JobLineItem.type == "cost",
            JobLineItem.is_committed == True,
        )
    ) or 0
    job_result = await db.execute(select(Job).where(Job.id == payload.job_id))
    job = job_result.scalar_one_or_none()
    if job:
        job.total_revenue = float(rev)
        job.total_cost = float(cost)
        job.gross_profit = float(rev) - float(cost)
        job.margin_pct = round((float(rev) - float(cost)) / float(rev) * 100, 1) if float(rev) else 0

    await db.flush()
    await db.refresh(invoice)
    return invoice


@router.post("/migrate-add-event-id")
async def migrate_add_event_id(db: AsyncSession = Depends(get_db)):
    async with engine.begin() as conn:
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'purchase_invoices' AND column_name = 'event_id'
                ) THEN
                    ALTER TABLE purchase_invoices ADD COLUMN event_id UUID REFERENCES events(id);
                END IF;
            END $$;
        """))
    result = await db.execute(
        select(PurchaseInvoice).where(
            PurchaseInvoice.event_id.is_(None),
            PurchaseInvoice.job_id.isnot(None),
        )
    )
    invoices = result.scalars().all()
    linked = 0
    for inv in invoices:
        ev_result = await db.execute(
            select(Event).where(Event.job_id == inv.job_id).limit(1)
        )
        ev = ev_result.scalar_one_or_none()
        if ev:
            inv.event_id = ev.id
            linked += 1
    await db.flush()
    return {"column_added": True, "invoices_linked": linked}


@router.get("/{invoice_id}/pay-form", response_class=HTMLResponse)
async def pay_form(request: Request, invoice_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseInvoice).where(PurchaseInvoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    return _page_templates.TemplateResponse(request, "partials/payment_voucher_prefilled.html", {
        "request": request,
        "invoice_number": inv.invoice_number,
        "vendor_name": inv.vendor_name,
        "vendor_id": str(inv.vendor_id) if inv.vendor_id else "",
        "job_id": str(inv.job_id) if inv.job_id else "",
        "purchase_invoice_id": str(inv.id),
        "amount": float(inv.total_amount),
        "currency": inv.currency,
        "today": date.today().isoformat(),
    })
