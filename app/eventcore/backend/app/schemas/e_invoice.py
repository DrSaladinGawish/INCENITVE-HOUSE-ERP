from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class EInvoiceLineCreate(BaseModel):
    invoice_type: str = Field(..., pattern="^(sales|purchase)$")
    sales_invoice_id: Optional[UUID] = None
    purchase_invoice_id: Optional[UUID] = None
    invoice_number: str
    issue_date: date
    total_amount: float
    vat_amount: float = 0
    net_amount: float
    eta_status: str = "pending"


class EInvoiceLineResponse(BaseModel):
    id: UUID
    invoice_type: str
    sales_invoice_id: Optional[UUID] = None
    purchase_invoice_id: Optional[UUID] = None
    invoice_number: str
    issue_date: date
    total_amount: float
    vat_amount: float
    net_amount: float
    eta_status: str
    is_synced: bool
    created_at: datetime

    model_config = {"from_attributes": True}
