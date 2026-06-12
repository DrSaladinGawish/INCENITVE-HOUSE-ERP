from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class PNRMasterBase(BaseModel):
    PNRNumber: str = Field(..., max_length=50)
    ClientCode: Optional[str] = Field(None, max_length=10)
    EventName: Optional[str] = Field(None, max_length=500)
    EventStartDate: Optional[date] = None
    EventEndDate: Optional[date] = None
    JobFolder: Optional[str] = Field(None, max_length=200)
    Year: Optional[int] = None
    Status: Optional[str] = Field(None, max_length=20)
    CurrencyCode: Optional[str] = Field(None, max_length=3)


class PNRMasterCreate(PNRMasterBase):
    pass


class PNRMasterUpdate(BaseModel):
    EventName: Optional[str] = None
    EventStartDate: Optional[date] = None
    EventEndDate: Optional[date] = None
    JobFolder: Optional[str] = None
    Year: Optional[int] = None
    Status: Optional[str] = None
    CurrencyCode: Optional[str] = None


class PNRMasterResponse(PNRMasterBase):
    class Config:
        from_attributes = True


class PNRBudgetLineItemBase(BaseModel):
    Year: Optional[int] = None
    JobFolder: Optional[str] = Field(None, max_length=500)
    FileName: Optional[str] = Field(None, max_length=500)
    SheetName: Optional[str] = Field(None, max_length=200)
    RowNumber: Optional[int] = None
    MainCategoryCode: Optional[str] = Field(None, max_length=10)
    SubCategoryCode: Optional[str] = Field(None, max_length=20)
    ClientCode: Optional[str] = Field(None, max_length=10)
    Description: Optional[str] = None
    Quantity: Optional[float] = None
    UnitPrice: Optional[float] = None
    Amount: Optional[float] = None
    CurrencyCode: Optional[str] = Field(None, max_length=3)


class PNRBudgetLineItemCreate(PNRBudgetLineItemBase):
    pass


class PNRBudgetLineItemUpdate(BaseModel):
    Year: Optional[int] = None
    JobFolder: Optional[str] = None
    FileName: Optional[str] = None
    SheetName: Optional[str] = None
    RowNumber: Optional[int] = None
    MainCategoryCode: Optional[str] = None
    SubCategoryCode: Optional[str] = None
    ClientCode: Optional[str] = None
    Description: Optional[str] = None
    Quantity: Optional[float] = None
    UnitPrice: Optional[float] = None
    Amount: Optional[float] = None
    CurrencyCode: Optional[str] = None


class PNRBudgetLineItemResponse(PNRBudgetLineItemBase):
    LineItemID: int

    class Config:
        from_attributes = True


class ServiceMainCategoryBase(BaseModel):
    MainCategoryCode: str = Field(..., max_length=10)
    MainCategoryName: str = Field(..., max_length=100)
    DisplayOrder: Optional[int] = None


class ServiceMainCategoryResponse(ServiceMainCategoryBase):
    class Config:
        from_attributes = True


class ServiceSubCategoryBase(BaseModel):
    SubCategoryCode: str = Field(..., max_length=20)
    MainCategoryCode: str = Field(..., max_length=10)
    SubCategoryName: str = Field(..., max_length=200)
    DefaultVendorCode: Optional[str] = Field(None, max_length=10)
    GLAccount: Optional[str] = Field(None, max_length=20)


class ServiceSubCategoryResponse(ServiceSubCategoryBase):
    class Config:
        from_attributes = True


class ServiceTypeBase(BaseModel):
    ServiceTypeCode: str = Field(..., max_length=10)
    ServiceName: str = Field(..., max_length=200)
    CostAccount: Optional[str] = Field(None, max_length=20)
    SubCategoryCode: Optional[str] = Field(None, max_length=20)


class ServiceTypeResponse(ServiceTypeBase):
    class Config:
        from_attributes = True
