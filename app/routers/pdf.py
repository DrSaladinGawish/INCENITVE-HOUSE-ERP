from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import SalesInvoice, PurchaseInvoice
from app.services.pdf_generator import generate_invoice_pdf

router = APIRouter(prefix="/api/v1/pdf", tags=["pdf"])


@router.get("/sales/{invoice_id}")
async def download_sales_invoice_pdf(invoice_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    inv = await db.get(SalesInvoice, invoice_id)
    if not inv: raise HTTPException(status_code=404, detail="Invoice not found")
    data = {
        "invoice_no": inv.invoice_no, "invoice_date": str(inv.invoice_date) if inv.invoice_date else "",
        "client_name": inv.client_name or inv.client_code or "", "due_date": str(inv.due_date) if inv.due_date else "",
        "total_amount": float(inv.total_amount or 0), "line_items": [{"description": f"Sales - {inv.category or 'N/A'}", "amount": float(inv.total_amount or 0)}],
    }
    pdf = generate_invoice_pdf(data)
    return Response(content=pdf.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=invoice_{inv.invoice_no}.pdf"})


@router.get("/purchase/{invoice_id}")
async def download_purchase_invoice_pdf(invoice_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    inv = await db.get(PurchaseInvoice, invoice_id)
    if not inv: raise HTTPException(status_code=404, detail="Invoice not found")
    data = {
        "invoice_no": inv.invoice_no, "invoice_date": str(inv.invoice_date) if inv.invoice_date else "",
        "client_name": inv.vendor_name or inv.vendor_code or "", "due_date": str(inv.due_date) if inv.due_date else "",
        "total_amount": float(inv.total_amount or 0), "line_items": [{"description": f"Purchase - {inv.category or 'N/A'}", "amount": float(inv.total_amount or 0)}],
    }
    pdf = generate_invoice_pdf(data)
    return Response(content=pdf.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=po_{inv.invoice_no}.pdf"})
