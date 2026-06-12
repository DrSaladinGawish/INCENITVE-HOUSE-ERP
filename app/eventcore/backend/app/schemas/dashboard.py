from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class KPIResponse(BaseModel):
    active_jobs: int
    total_revenue_qtd: float
    total_cost_qtd: float
    avg_margin_pct: float
    unlinked_purchases: int
    unreconciled_transactions: int
    cash_position: float


class ClientFlipperItem(BaseModel):
    client_id: UUID
    client_name: str
    total_revenue: float
    margin_pct: float
    job_count: int


class AlertResponse(BaseModel):
    id: UUID
    type: str
    message: str
    entity_type: str
    entity_id: UUID
    action_url: str
