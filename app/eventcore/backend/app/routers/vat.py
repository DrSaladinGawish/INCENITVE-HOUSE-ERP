from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.vat_return import VATReturn
from app.models.sales_invoice import SalesInvoice
from app.models.purchase_invoice import PurchaseInvoice
from app.schemas.vat import (
    VATReturnCreate, VATReturnResponse,
    VATCalculationRequest, VATCalculationResponse,
)

router = APIRouter(prefix="/api/v1/vat", tags=["VAT"])


@router.post("/returns", response_model=VATReturnResponse, status_code=201)
async def create_vat_return(payload: VATReturnCreate, db: AsyncSession = Depends(get_db)):
    vr = VATReturn(**payload.model_dump())
    db.add(vr)
    await db.flush()
    await db.refresh(vr)
    return vr


@router.get("/returns", response_model=list[VATReturnResponse])
async def list_vat_returns(
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(VATReturn).order_by(VATReturn.period_start.desc())
    if status:
        q = q.where(VATReturn.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/returns/{return_id}", response_model=VATReturnResponse)
async def get_vat_return(return_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VATReturn).where(VATReturn.id == return_id))
    vr = result.scalar_one_or_none()
    if not vr:
        raise HTTPException(404, "VAT return not found")
    return vr


@router.post("/calculate", response_model=VATCalculationResponse)
async def calculate_vat(payload: VATCalculationRequest, db: AsyncSession = Depends(get_db)):
    period_start, period_end = payload.period_start, payload.period_end

    sales_count = await db.scalar(
        select(func.count(SalesInvoice.id))
        .where(and_(SalesInvoice.invoice_date >= period_start, SalesInvoice.invoice_date <= period_end))
    ) or 0

    sales_vat = await db.scalar(
        select(func.coalesce(func.sum(SalesInvoice.vat_amount), 0))
        .where(and_(SalesInvoice.invoice_date >= period_start, SalesInvoice.invoice_date <= period_end))
    ) or 0

    purchase_count = await db.scalar(
        select(func.count(PurchaseInvoice.id))
        .where(and_(PurchaseInvoice.invoice_date >= period_start, PurchaseInvoice.invoice_date <= period_end))
    ) or 0

    purchase_vat = await db.scalar(
        select(func.coalesce(func.sum(PurchaseInvoice.vat_amount), 0))
        .where(and_(PurchaseInvoice.invoice_date >= period_start, PurchaseInvoice.invoice_date <= period_end))
    ) or 0

    return VATCalculationResponse(
        period_start=period_start,
        period_end=period_end,
        sales_invoices_count=sales_count,
        total_sales_vat=float(sales_vat),
        purchase_invoices_count=purchase_count,
        total_purchase_vat=float(purchase_vat),
        net_vat_due=float(sales_vat) - float(purchase_vat),
    )


@router.patch("/returns/{return_id}/submit")
async def submit_vat_return(return_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VATReturn).where(VATReturn.id == return_id))
    vr = result.scalar_one_or_none()
    if not vr:
        raise HTTPException(404, "VAT return not found")
    vr.status = "submitted"
    await db.flush()
    return {"status": "submitted", "id": str(return_id)}
