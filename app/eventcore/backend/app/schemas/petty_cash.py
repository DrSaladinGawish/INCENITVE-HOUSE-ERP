from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class PettyCashCreate(BaseModel):
    job_id: UUID = Field(..., description="MUST be tagged to a job.")
    staff_name: str
    expense_date: date
    category: str
    description: str
    amount: float
    currency: str = "EGP"
    has_receipt: bool = False


class PettyCashResponse(BaseModel):
    id: UUID
    job_id: UUID
    staff_name: str
    expense_date: date
    category: str
    description: str
    amount: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
