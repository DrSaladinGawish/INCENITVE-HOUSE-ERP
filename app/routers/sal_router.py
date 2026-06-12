from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import sal_service
from app.schemas.sal import (
    ClientCreate, ClientUpdate, ClientResponse,
    SalesInvoiceCreate, SalesInvoiceUpdate, SalesInvoiceResponse, SalesInvoiceList,
)

router = APIRouter(prefix="/api/sal", tags=["Sales"])


@router.get("/clients", response_model=list[ClientResponse])
def list_clients(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return sal_service.get_clients(db, skip=skip, limit=limit)


@router.get("/clients/{client_code}", response_model=ClientResponse)
def get_client(client_code: str, db: Session = Depends(get_db)):
    client = sal_service.get_client(db, client_code)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.post("/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(data: ClientCreate, db: Session = Depends(get_db)):
    return sal_service.create_client(db, data)


@router.put("/clients/{client_code}", response_model=ClientResponse)
def update_client(client_code: str, data: ClientUpdate, db: Session = Depends(get_db)):
    client = sal_service.update_client(db, client_code, data)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.delete("/clients/{client_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_code: str, db: Session = Depends(get_db)):
    if not sal_service.delete_client(db, client_code):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")


@router.get("/invoices", response_model=SalesInvoiceList)
def list_invoices(
    client_code: str | None = Query(None),
    pnr_number: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = sal_service.get_sales_invoices(db, client_code=client_code, pnr_number=pnr_number, skip=skip, limit=page_size)
    return SalesInvoiceList(items=items, total=total, page=page, page_size=page_size)


@router.get("/invoices/{invoice_id}", response_model=SalesInvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = sal_service.get_sales_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@router.post("/invoices", response_model=SalesInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(data: SalesInvoiceCreate, db: Session = Depends(get_db)):
    return sal_service.create_sales_invoice(db, data)


@router.put("/invoices/{invoice_id}", response_model=SalesInvoiceResponse)
def update_invoice(invoice_id: int, data: SalesInvoiceUpdate, db: Session = Depends(get_db)):
    invoice = sal_service.update_sales_invoice(db, invoice_id, data)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    if not sal_service.delete_sales_invoice(db, invoice_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
