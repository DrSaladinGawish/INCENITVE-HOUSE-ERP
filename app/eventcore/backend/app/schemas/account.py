from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class JournalVoucherCreate(BaseModel):
    voucher_number: str
    voucher_date: date
    job_id: Optional[UUID] = None
    description: Optional[str] = None
    debit_account: str
    credit_account: str
    amount: float
    currency: str = "EGP"


class JournalVoucherResponse(BaseModel):
    id: UUID
    voucher_number: str
    voucher_date: date
    job_id: Optional[UUID] = None
    description: Optional[str] = None
    debit_account: str
    credit_account: str
    amount: float
    currency: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TrialBalanceItem(BaseModel):
    account_code: str
    account_name: str
    debit: float
    credit: float
    balance: float


class ProfitLossItem(BaseModel):
    category: str
    revenue: float = 0
    cost: float = 0
    gross_profit: float = 0


class ChartAccountCreate(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    is_cos: bool = False
    description: Optional[str] = None


class ChartAccountResponse(BaseModel):
    id: UUID
    account_code: str
    account_name: str
    account_type: str
    is_cos: bool
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
