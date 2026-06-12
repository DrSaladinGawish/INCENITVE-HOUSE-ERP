from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine
from app.models.e_invoice import EInvoiceLine
from app.models.purchase_invoice import PurchaseInvoice
from app.models.sales_invoice import SalesInvoice
from app.schemas.e_invoice import EInvoiceLineCreate, EInvoiceLineResponse


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

router = APIRouter(prefix="/api/v1/e-invoice", tags=["E-Invoice"])


@router.post("/lines", response_model=EInvoiceLineResponse, status_code=201)
async def create_einvoice_line(
    payload: EInvoiceLineCreate,
    db: AsyncSession = Depends(get_db),
):
    line = EInvoiceLine(
        invoice_type=payload.invoice_type,
        sales_invoice_id=payload.sales_invoice_id,
        purchase_invoice_id=payload.purchase_invoice_id,
        invoice_number=payload.invoice_number,
        issue_date=payload.issue_date,
        total_amount=payload.total_amount,
        vat_amount=payload.vat_amount,
        net_amount=payload.net_amount,
        eta_status=payload.eta_status,
    )
    db.add(line)
    await db.flush()
    await db.refresh(line)
    return line


@router.get("/lines", response_model=list[EInvoiceLineResponse])
async def list_einvoice_lines(
    invoice_type: str | None = Query(None),
    eta_status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(EInvoiceLine).order_by(EInvoiceLine.created_at.desc())
    if invoice_type:
        q = q.where(EInvoiceLine.invoice_type == invoice_type)
    if eta_status:
        q = q.where(EInvoiceLine.eta_status == eta_status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/lines/{line_id}", response_model=EInvoiceLineResponse)
async def get_einvoice_line(line_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EInvoiceLine).where(EInvoiceLine.id == line_id))
    line = result.scalar_one_or_none()
    if not line:
        raise HTTPException(404, "E-Invoice line not found")
    return line


@router.post("/migrate-generate-missing")
async def migrate_generate_missing(db: AsyncSession = Depends(get_db)):
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS e_invoice_lines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                invoice_type VARCHAR(20) NOT NULL,
                sales_invoice_id UUID REFERENCES sales_invoices(id),
                purchase_invoice_id UUID REFERENCES purchase_invoices(id),
                invoice_number VARCHAR(100) NOT NULL,
                issue_date DATE NOT NULL,
                total_amount NUMERIC(15,2) NOT NULL,
                vat_amount NUMERIC(15,2) DEFAULT 0,
                net_amount NUMERIC(15,2) NOT NULL,
                eta_status VARCHAR(20) DEFAULT 'pending',
                is_synced BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))

    result = await db.execute(
        select(PurchaseInvoice).where(
            PurchaseInvoice.id.notin_(
                select(EInvoiceLine.purchase_invoice_id).where(
                    EInvoiceLine.purchase_invoice_id.isnot(None)
                )
            )
        )
    )
    missing = result.scalars().all()
    generated = 0
    for inv in missing:
        line = EInvoiceLine(
            invoice_type="purchase",
            purchase_invoice_id=inv.id,
            invoice_number=inv.invoice_number,
            issue_date=inv.invoice_date,
            total_amount=float(inv.total_amount or 0),
            vat_amount=float(inv.vat_amount or 0),
            net_amount=float((inv.total_amount or 0) - (inv.vat_amount or 0)),
            eta_status="generated",
            is_synced=False,
        )
        db.add(line)
        generated += 1
    await db.flush()
    return {"table_created": True, "lines_generated": generated}
