from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class BankBase(BaseModel):
    BankCode: str = Field(..., max_length=10)
    BankName: str = Field(..., max_length=200)
    GLAccount: Optional[str] = Field(None, max_length=20)
    IsActive: bool = True


class BankCreate(BankBase):
    pass


class BankUpdate(BaseModel):
    BankName: Optional[str] = None
    GLAccount: Optional[str] = None
    IsActive: Optional[bool] = None


class BankResponse(BankBase):
    class Config:
        from_attributes = True


class BankTransactionBase(BaseModel):
    TransactionDate: date
    Payee: Optional[str] = Field(None, max_length=200)
    DocumentType: Optional[str] = Field(None, max_length=100)
    DocumentNumber: Optional[str] = Field(None, max_length=50)
    Withdrawal: Optional[float] = None
    Deposit: Optional[float] = None
    RunningBalance: Optional[float] = None
    TransactionType: Optional[str] = Field(None, max_length=50)
    JVNumber: Optional[str] = Field(None, max_length=50)
    Narration: Optional[str] = None
    DrAccount: Optional[str] = Field(None, max_length=20)
    CrAccount: Optional[str] = Field(None, max_length=20)
    FromSubCategory: Optional[str] = Field(None, max_length=200)
    ToSubCategory: Optional[str] = Field(None, max_length=200)
    BankCode: Optional[str] = Field(None, max_length=10)
    CurrencyCode: str = "EGP"


class BankTransactionCreate(BankTransactionBase):
    pass


class BankTransactionResponse(BankTransactionBase):
    TransactionID: int

    class Config:
        from_attributes = True


class BankTransactionList(BaseModel):
    items: list[BankTransactionResponse]
    total: int
    page: int = 1
    page_size: int = 50
