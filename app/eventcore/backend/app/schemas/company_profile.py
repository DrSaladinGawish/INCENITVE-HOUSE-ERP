from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CompanyProfileCreate(BaseModel):
    company_name: str
    legal_name: str
    tax_number: str
    commercial_register: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str = "Cairo"
    country: str = "Egypt"
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    default_currency: str = "EGP"
    vat_rate: float = 14.0


class CompanyProfileResponse(BaseModel):
    id: UUID
    company_name: str
    legal_name: str
    tax_number: str
    commercial_register: Optional[str] = None
    address_line1: str
    city: str
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    default_currency: str
    vat_rate: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
