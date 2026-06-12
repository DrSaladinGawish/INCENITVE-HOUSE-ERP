from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ClientCreate(BaseModel):
    client_code: str
    name: str
    industry: Optional[str] = None
    vat_number: Optional[str] = None
    default_currency: str = "EGP"
    credit_limit: float = 0
    payment_terms: int = 30


class ClientResponse(BaseModel):
    id: UUID
    client_code: str
    name: str
    industry: Optional[str] = None
    vat_number: Optional[str] = None
    default_currency: str
    credit_limit: float
    payment_terms: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
