"""PDF export router — generates PDF documents for invoices, quotations, P&L."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.sales_invoice import SalesInvoice
from app.models.quotation import Quotation
from app.models.job import Job
from app.services.pdf_generator import (
    generate_invoice_pdf,
    generate_quotation_pdf,
    generate_pnl_report,
)

router = APIRouter(prefix="/api/v1/pdf", tags=["PDF Export"])


@router.get("/sales-invoice/{invoice_id}")
async def export_sales_invoice_pdf(invoice_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SalesInvoice).where(SalesInvoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Sales invoice not found")
    pdf_bytes = generate_invoice_pdf(invoice_id, {
        "invoice_number": inv.invoice_number,
        "invoice_date": str(inv.invoice_date),
        "total_amount": float(inv.total_amount),
        "currency": inv.currency,
    })
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="invoice-{inv.invoice_number}.pdf"'},
    )


@router.get("/quotation/{quotation_id}")
async def export_quotation_pdf(quotation_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Quotation).where(Quotation.id == quotation_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(404, "Quotation not found")
    pdf_bytes = generate_quotation_pdf(quotation_id, {
        "quote_number": q.quote_number,
        "event_name": q.event_name,
        "total_amount": float(q.total_amount),
        "currency": q.currency,
    })
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="quotation-{q.quote_number}.pdf"'},
    )


@router.get("/job-pnl/{job_id}")
async def export_pnl_pdf(job_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    pdf_bytes = generate_pnl_report({
        "job_code": job.job_code,
        "event_name": job.event_name,
        "total_revenue": float(job.total_revenue),
        "total_cost": float(job.total_cost),
        "gross_profit": float(job.gross_profit),
        "margin_pct": float(job.margin_pct),
    })
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="pnl-{job.job_code}.pdf"'},
    )
