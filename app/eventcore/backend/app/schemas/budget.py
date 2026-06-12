from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class BudgetPeriodCreate(BaseModel):
    fiscal_year: int
    quarter: Optional[int] = None
    month: Optional[int] = None
    label: str
    start_date: date
    end_date: date


class BudgetPeriodResponse(BaseModel):
    id: UUID
    fiscal_year: int
    quarter: Optional[int] = None
    month: Optional[int] = None
    label: str
    start_date: date
    end_date: date
    is_closed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetLineCreate(BaseModel):
    event_id: UUID
    job_id: UUID
    budget_period_id: Optional[UUID] = None
    category: str
    description: Optional[str] = None
    budgeted_amount: float
    notes: Optional[str] = None


class BudgetLineResponse(BaseModel):
    id: UUID
    event_id: UUID
    job_id: UUID
    budget_period_id: Optional[UUID] = None
    category: str
    description: Optional[str] = None
    budgeted_amount: float
    actual_amount: float
    committed_amount: float
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetCommitmentCreate(BaseModel):
    budget_line_id: UUID
    purchase_invoice_id: Optional[UUID] = None
    sales_invoice_id: Optional[UUID] = None
    amount: float
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None


class BudgetCommitmentResponse(BaseModel):
    id: UUID
    budget_line_id: UUID
    purchase_invoice_id: Optional[UUID] = None
    sales_invoice_id: Optional[UUID] = None
    amount: float
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}
