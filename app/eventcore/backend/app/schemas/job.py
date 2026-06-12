from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class JobCreate(BaseModel):
    client_id: UUID
    event_name: str
    event_dates: Optional[str] = None
    description: Optional[str] = None
    margin_target: float = 35.0


class JobResponse(BaseModel):
    id: UUID
    job_code: str
    year: int
    client_id: UUID
    sequence: int
    event_name: str
    description: Optional[str] = None
    total_revenue: float
    total_cost: float
    gross_profit: float
    margin_pct: float
    status: str
    margin_target: float
    created_at: datetime

    model_config = {"from_attributes": True}


class JobPNLResponse(BaseModel):
    job_id: UUID
    job_code: str
    event_name: str
    total_revenue: float
    total_cost: float
    gross_profit: float
    margin_pct: float
    revenue_by_category: list[dict]
    cost_by_category: list[dict]
    meta: dict = {
        "basis": "invoice_accrual",
        "coverage_pct": 15.3,
        "missing_reason": "Source CSV export stripped monetary values",
        "confidence": "low",
    }
