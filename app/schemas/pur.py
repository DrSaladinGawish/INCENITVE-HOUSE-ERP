from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class VendorBase(BaseModel):
    VendorCode: str = Field(..., max_length=10)
    VendorName: str = Field(..., max_length=200)
    TaxID: Optional[str] = Field(None, max_length=50)
    TaxRegisterNo: Optional[str] = Field(None, max_length=50)
    Address: Optional[str] = Field(None, max_length=500)
    Telephone: Optional[str] = Field(None, max_length=50)
    Email: Optional[str] = Field(None, max_length=200)
    Branch: Optional[str] = Field(None, max_length=100)
    BankName: Optional[str] = Field(None, max_length=100)
    IBAN: Optional[str] = Field(None, max_length=50)
    EGPAccountNo: Optional[str] = Field(None, max_length=50)
    USDAccountNo: Optional[str] = Field(None, max_length=50)
    VendorType: Optional[str] = Field(None, max_length=50)
    PostingAccount: Optional[str] = Field(None, max_length=20)
    ExpenseAccount: Optional[str] = Field(None, max_length=20)
    PaymentTerms: Optional[str] = Field(None, max_length=100)


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    VendorName: Optional[str] = None
    TaxID: Optional[str] = None
    TaxRegisterNo: Optional[str] = None
    Address: Optional[str] = None
    Telephone: Optional[str] = None
    Email: Optional[str] = None
    Branch: Optional[str] = None
    BankName: Optional[str] = None
    IBAN: Optional[str] = None
    EGPAccountNo: Optional[str] = None
    USDAccountNo: Optional[str] = None
    VendorType: Optional[str] = None
    PostingAccount: Optional[str] = None
    ExpenseAccount: Optional[str] = None
    PaymentTerms: Optional[str] = None
    IsActive: Optional[bool] = None


class VendorResponse(VendorBase):
    IsActive: bool

    class Config:
        from_attributes = True


class PurchaseVoucherLineBase(BaseModel):
    ServiceTypeCode: Optional[str] = Field(None, max_length=10)
    VendorCode: Optional[str] = Field(None, max_length=10)
    ItemNarration: Optional[str] = None
    Quantity: Optional[float] = None
    NoOfNights: Optional[int] = None
    UnitPrice: Optional[float] = None
    SubTotal: Optional[float] = None
    VATAmount: Optional[float] = None


class PurchaseVoucherLineCreate(PurchaseVoucherLineBase):
    pass


class PurchaseVoucherLineResponse(PurchaseVoucherLineBase):
    VoucherLineID: int
    VoucherID: int

    class Config:
        from_attributes = True


class PurchaseVoucherBase(BaseModel):
    VoucherNumber: Optional[str] = Field(None, max_length=50)
    DocumentNumber: Optional[str] = Field(None, max_length=50)
    PNRNumber: Optional[str] = Field(None, max_length=50)
    EventName: Optional[str] = Field(None, max_length=500)
    InvoiceDate: Optional[date] = None
    TotalValue: Optional[float] = None
    CurrencyCode: Optional[str] = Field(None, max_length=3)


class PurchaseVoucherCreate(PurchaseVoucherBase):
    lines: list[PurchaseVoucherLineCreate] = []


class PurchaseVoucherResponse(PurchaseVoucherBase):
    VoucherID: int
    lines: list[PurchaseVoucherLineResponse] = []

    class Config:
        from_attributes = True


class PurchaseVoucherList(BaseModel):
    items: list[PurchaseVoucherResponse]
    total: int
    page: int = 1
    page_size: int = 50
