from pydantic import BaseModel
from typing import Optional


class DashboardSummary(BaseModel):
    total_pnrs: int
    active_pnrs: int
    total_sales: float
    total_purchases: float
    bank_balance: float
    outstanding_receivables: float
    total_clients: int
    total_vendors: int
