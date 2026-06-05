from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    ClientCode: str = Field(..., max_length=10)
    ClientName: str = Field(..., max_length=200)
    TaxID: Optional[str] = Field(None, max_length=50)
    TaxRegisterNo: Optional[str] = Field(None, max_length=50)
    Address: Optional[str] = Field(None, max_length=500)
    Telephone: Optional[str] = Field(None, max_length=50)
    Email: Optional[str] = Field(None, max_length=200)
    ContactPerson: Optional[str] = Field(None, max_length=200)
    PostingAccount: Optional[str] = Field(None, max_length=20)
    ExpenseAccount: Optional[str] = Field(None, max_length=20)
    PaymentTerms: Optional[str] = Field(None, max_length=100)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    ClientName: Optional[str] = None
    TaxID: Optional[str] = None
    TaxRegisterNo: Optional[str] = None
    Address: Optional[str] = None
    Telephone: Optional[str] = None
    Email: Optional[str] = None
    ContactPerson: Optional[str] = None
    PostingAccount: Optional[str] = None
    ExpenseAccount: Optional[str] = None
    PaymentTerms: Optional[str] = None
    IsActive: Optional[bool] = None


class ClientResponse(ClientBase):
    IsActive: bool

    class Config:
        from_attributes = True


class SalesInvoiceLineBase(BaseModel):
    ServiceTypeCode: Optional[str] = Field(None, max_length=10)
    LineAmount: Optional[float] = None


class SalesInvoiceLineCreate(SalesInvoiceLineBase):
    pass


class SalesInvoiceLineResponse(SalesInvoiceLineBase):
    InvoiceLineID: int
    InvoiceID: int

    class Config:
        from_attributes = True


class SalesInvoiceBase(BaseModel):
    InvoiceNumber: Optional[str] = Field(None, max_length=50)
    PNRNumber: Optional[str] = Field(None, max_length=50)
    ClientCode: Optional[str] = Field(None, max_length=10)
    EventName: Optional[str] = Field(None, max_length=500)
    InvoiceDate: Optional[date] = None
    DueDate: Optional[date] = None
    TotalValue: Optional[float] = None
    CollectedAmount: Optional[float] = None
    PaymentStatus: Optional[str] = Field(None, max_length=20)
    CurrencyCode: Optional[str] = Field(None, max_length=3)


class SalesInvoiceCreate(SalesInvoiceBase):
    lines: list[SalesInvoiceLineCreate] = []


class SalesInvoiceResponse(SalesInvoiceBase):
    InvoiceID: int
    lines: list[SalesInvoiceLineResponse] = []

    class Config:
        from_attributes = True


class SalesInvoiceList(BaseModel):
    items: list[SalesInvoiceResponse]
    total: int
    page: int = 1
    page_size: int = 50
