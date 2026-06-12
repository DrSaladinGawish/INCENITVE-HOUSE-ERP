from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.sales_invoice import SalesInvoice, SalesInvoiceLineItem
from app.schemas.sales_invoice import (
    SalesInvoiceCreate, SalesInvoiceUpdate, SalesInvoiceResponse,
    SalesInvoiceLineItemResponse,
)

router = APIRouter(prefix="/api/v1/sales-invoices", tags=["Sales Invoices"])


@router.post("", response_model=SalesInvoiceResponse, status_code=201)
async def create_sales_invoice(payload: SalesInvoiceCreate, db: AsyncSession = Depends(get_db)):
    line_items_data = payload.line_items
    payload_dict = payload.model_dump(exclude={"line_items"})
    inv = SalesInvoice(**payload_dict)
    db.add(inv)
    await db.flush()

    for i, li in enumerate(line_items_data):
        item = SalesInvoiceLineItem(
            invoice_id=inv.id,
            description=li.description,
            quantity=li.quantity,
            unit_price=li.unit_price,
            total_amount=li.total_amount,
            sort_order=i,
        )
        db.add(item)
    await db.flush()
    await db.refresh(inv)
    return inv


@router.get("", response_model=list[SalesInvoiceResponse])
async def list_sales_invoices(
    job_id: UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(SalesInvoice)
        .options(selectinload(SalesInvoice.line_items))
        .order_by(SalesInvoice.created_at.desc())
    )
    if job_id:
        q = q.where(SalesInvoice.job_id == job_id)
    if status:
        q = q.where(SalesInvoice.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{invoice_id}", response_model=SalesInvoiceResponse)
async def get_sales_invoice(invoice_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SalesInvoice)
        .options(selectinload(SalesInvoice.line_items))
        .where(SalesInvoice.id == invoice_id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Sales invoice not found")
    return inv


@router.patch("/{invoice_id}", response_model=SalesInvoiceResponse)
async def update_sales_invoice(
    invoice_id: UUID,
    payload: SalesInvoiceUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SalesInvoice).where(SalesInvoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Sales invoice not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(inv, key, val)
    await db.flush()
    await db.refresh(inv)
    return inv


@router.post("/eta-import")
async def import_eta_csv(db: AsyncSession = Depends(get_db)):
    return {"status": "stub", "message": "ETA CSV import not yet implemented"}
