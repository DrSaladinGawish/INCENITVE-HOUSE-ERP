from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class BankTransactionResponse(BaseModel):
    id: UUID
    bank_account: str
    transaction_date: date
    description: str
    amount: float
    currency: str
    counterparty: Optional[str] = None
    is_reconciled: bool
    linked_job_id: Optional[UUID] = None
    linked_method: Optional[str] = None
    match_confidence: Optional[float] = None

    model_config = {"from_attributes": True}


class BankTransactionLinkRequest(BaseModel):
    job_id: UUID
    linked_method: str = "drag_drop"
