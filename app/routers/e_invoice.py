from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ihe_models import SalesInvoice
from app.services.e_invoice_service import generate_e_invoice_by_number

router = APIRouter(prefix="/e-invoice", tags=["E-Invoice"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def e_invoice_dashboard(request: Request, db: Session = Depends(get_db)):
    invoices = db.query(SalesInvoice).order_by(SalesInvoice.InvoiceDate.desc()).limit(50).all()
    return templates.TemplateResponse("e_invoice/dashboard.html", {"request": request, "invoices": invoices})


@router.get("/generate/{invoice_number}")
def generate_xml(invoice_number: str, db: Session = Depends(get_db)):
    xml_str = generate_e_invoice_by_number(db, invoice_number)
    if xml_str is None:
        return {"detail": f"Invoice {invoice_number} not found"}
    return PlainTextResponse(content=xml_str, media_type="application/xml")


@router.get("/download/{invoice_number}")
def download_xml(invoice_number: str, db: Session = Depends(get_db)):
    xml_str = generate_e_invoice_by_number(db, invoice_number)
    if xml_str is None:
        return {"detail": f"Invoice {invoice_number} not found"}
    from fastapi.responses import Response
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="einvoice_{invoice_number}.xml"'},
    )
