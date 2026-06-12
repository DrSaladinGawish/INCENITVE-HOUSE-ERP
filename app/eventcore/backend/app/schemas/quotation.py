from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class QuotationLineItemCreate(BaseModel):
    category: str
    description: str
    quantity: float = 1
    unit_price: float
    total_amount: float = 0
    vendor_estimate: Optional[str] = None
    notes: Optional[str] = None


class QuotationLineItemResponse(BaseModel):
    id: UUID
    quotation_id: UUID
    category: str
    description: str
    quantity: float
    unit_price: float
    total_amount: float
    vendor_estimate: Optional[str] = None
    notes: Optional[str] = None
    sort_order: int

    model_config = {"from_attributes": True}


class QuotationCreate(BaseModel):
    client_id: UUID
    quote_number: str
    quote_date: date
    valid_until: Optional[date] = None
    event_name: str
    event_dates: Optional[str] = None
    destination: Optional[str] = None
    pax_count: Optional[int] = None
    subtotal: float = 0
    vat_amount: float = 0
    total_amount: float = 0
    line_items: list[QuotationLineItemCreate] = []


class QuotationUpdate(BaseModel):
    status: Optional[str] = None
    subtotal: Optional[float] = None
    vat_amount: Optional[float] = None
    total_amount: Optional[float] = None


class QuotationResponse(BaseModel):
    id: UUID
    quote_number: str
    quote_date: date
    valid_until: Optional[date] = None
    client_id: UUID
    event_name: str
    event_dates: Optional[str] = None
    destination: Optional[str] = None
    pax_count: Optional[int] = None
    subtotal: float
    vat_amount: float
    total_amount: float
    status: str
    converted_to_job_id: Optional[UUID] = None
    created_at: datetime
    line_items: list[QuotationLineItemResponse] = []

    model_config = {"from_attributes": True}
