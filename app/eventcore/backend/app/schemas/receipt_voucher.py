from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class ReceiptVoucherCreate(BaseModel):
    voucher_number: str = Field(..., description="Unique voucher identifier")
    job_id: UUID = Field(..., description="MUST be tagged to a job.")
    client_id: UUID
    sales_invoice_id: Optional[UUID] = None
    receipt_date: date
    amount: float
    currency: str = "EGP"
    payment_method: Optional[str] = None
    bank_account: Optional[str] = None
    created_by: Optional[UUID] = None


class ReceiptVoucherResponse(BaseModel):
    id: UUID
    voucher_number: str
    job_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    sales_invoice_id: Optional[UUID] = None
    receipt_date: date
    amount: float
    currency: str
    payment_method: Optional[str] = None
    bank_account: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
