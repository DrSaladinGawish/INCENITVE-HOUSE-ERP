from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class VATReturnCreate(BaseModel):
    period_start: date
    period_end: date
    total_sales_vat: float = 0
    total_purchase_vat: float = 0
    net_vat_due: float = 0
    status: str = "draft"


class VATReturnResponse(BaseModel):
    id: UUID
    period_start: date
    period_end: date
    total_sales_vat: float
    total_purchase_vat: float
    net_vat_due: float
    status: str
    submitted_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VATCalculationRequest(BaseModel):
    period_start: date
    period_end: date


class VATCalculationResponse(BaseModel):
    period_start: date
    period_end: date
    sales_invoices_count: int
    total_sales_vat: float
    purchase_invoices_count: int
    total_purchase_vat: float
    net_vat_due: float
    status: str = "calculated"
