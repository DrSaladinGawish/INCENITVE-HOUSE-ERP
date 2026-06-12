from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class PurchaseInvoiceCreate(BaseModel):
    job_id: Optional[UUID] = Field(None, description="Must be linked to a job. Unlinked invoices show a critical alert.")
    event_id: Optional[UUID] = None
    vendor_name: str
    vendor_id: Optional[UUID] = None
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    subtotal: float
    vat_amount: float = 0
    total_amount: float
    currency: str = "EGP"
    exchange_rate: float = 1


class PurchaseInvoiceResponse(BaseModel):
    id: UUID
    job_id: Optional[UUID]
    event_id: Optional[UUID] = None
    vendor_name: str
    invoice_number: str
    invoice_date: date
    total_amount: float
    status: str
    linked_method: Optional[str] = None
    linked_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PurchaseInvoiceLinkRequest(BaseModel):
    job_id: UUID
    linked_method: str = "manual"
