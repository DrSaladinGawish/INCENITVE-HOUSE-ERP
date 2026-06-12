from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChartOfAccountsBase(BaseModel):
    AccountCode: str = Field(..., max_length=20)
    AccountName: str = Field(..., max_length=200)
    AccountType: str = Field(..., max_length=50)
    ParentAccount: Optional[str] = Field(None, max_length=20)
    IsControlAccount: bool = False
    CurrencyCode: Optional[str] = Field(None, max_length=3)


class ChartOfAccountsResponse(ChartOfAccountsBase):
    class Config:
        from_attributes = True


class JournalVoucherLineBase(BaseModel):
    AccountCode: Optional[str] = Field(None, max_length=20)
    DebitAmount: Optional[float] = None
    CreditAmount: Optional[float] = None
    Narration: Optional[str] = None
    PNRNumber: Optional[str] = Field(None, max_length=50)


class JournalVoucherLineCreate(JournalVoucherLineBase):
    pass


class JournalVoucherLineResponse(JournalVoucherLineBase):
    JVLineID: int
    JVNumber: str

    class Config:
        from_attributes = True


class JournalVoucherBase(BaseModel):
    JVNumber: str = Field(..., max_length=50)
    JVDate: Optional[date] = None
    Narration: Optional[str] = None
    TotalDebit: Optional[float] = None
    TotalCredit: Optional[float] = None


class JournalVoucherCreate(JournalVoucherBase):
    lines: list[JournalVoucherLineCreate] = []


class JournalVoucherResponse(JournalVoucherBase):
    lines: list[JournalVoucherLineResponse] = []

    class Config:
        from_attributes = True


class JournalVoucherUpdate(BaseModel):
    JVDate: Optional[date] = None
    Narration: Optional[str] = None
    TotalDebit: Optional[float] = None
    TotalCredit: Optional[float] = None


class JournalVoucherList(BaseModel):
    items: list[JournalVoucherResponse]
    total: int
    page: int = 1
    page_size: int = 50


class EmployeeBase(BaseModel):
    EmployeeCode: str = Field(..., max_length=10)
    EmployeeName: str = Field(..., max_length=200)
    EmployeeType: str = Field(..., max_length=20)
    PostingAccount: Optional[str] = Field(None, max_length=20)
    ExpenseAccount: Optional[str] = Field(None, max_length=20)


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    EmployeeName: Optional[str] = None
    EmployeeType: Optional[str] = None
    PostingAccount: Optional[str] = None
    ExpenseAccount: Optional[str] = None
    IsActive: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    IsActive: bool

    class Config:
        from_attributes = True
