from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class SalesInvoiceLineItemCreate(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float = 0
    total_amount: float = 0


class SalesInvoiceLineItemResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    description: str
    quantity: float
    unit_price: float
    total_amount: float
    sort_order: int

    model_config = {"from_attributes": True}


class SalesInvoiceCreate(BaseModel):
    job_id: UUID
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    client_id: UUID
    client_vat: Optional[str] = None
    subtotal: float
    vat_amount: float = 0
    total_amount: float
    currency: str = "EGP"
    line_items: list[SalesInvoiceLineItemCreate] = []


class SalesInvoiceUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    collected_amount: Optional[float] = None
    collected_date: Optional[date] = None


class SalesInvoiceResponse(BaseModel):
    id: UUID
    job_id: UUID
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    client_id: UUID
    client_vat: Optional[str] = None
    subtotal: float
    vat_amount: float
    total_amount: float
    currency: str
    status: str
    payment_status: str
    collected_amount: float
    created_at: datetime
    line_items: list[SalesInvoiceLineItemResponse] = []

    model_config = {"from_attributes": True}
