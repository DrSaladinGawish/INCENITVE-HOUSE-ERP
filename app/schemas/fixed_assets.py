from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class AssetCategoryBase(BaseModel):
    CategoryCode: str = Field(..., max_length=20)
    CategoryName: str = Field(..., max_length=200)
    DefaultUsefulLife: Optional[int] = None
    DefaultDepreciationRate: Optional[float] = None
    GLAssetAccount: Optional[str] = Field(None, max_length=20)
    GLDepreciationAccount: Optional[str] = Field(None, max_length=20)
    GLAccumulatedDepAccount: Optional[str] = Field(None, max_length=20)


class AssetCategoryCreate(AssetCategoryBase):
    pass


class AssetCategoryUpdate(BaseModel):
    CategoryCode: Optional[str] = None
    CategoryName: Optional[str] = None
    DefaultUsefulLife: Optional[int] = None
    DefaultDepreciationRate: Optional[float] = None
    GLAssetAccount: Optional[str] = None
    GLDepreciationAccount: Optional[str] = None
    GLAccumulatedDepAccount: Optional[str] = None
    IsActive: Optional[bool] = None


class AssetCategoryResponse(AssetCategoryBase):
    CategoryID: int
    IsActive: bool

    class Config:
        from_attributes = True


class AssetBase(BaseModel):
    AssetCode: str = Field(..., max_length=50)
    AssetName: str = Field(..., max_length=500)
    CategoryID: int
    PurchaseDate: date
    PurchaseCost: float
    SalvageValue: float = 0
    UsefulLifeYears: int
    DepreciationMethod: str = "StraightLine"
    Location: Optional[str] = Field(None, max_length=200)
    SerialNumber: Optional[str] = Field(None, max_length=100)
    VendorCode: Optional[str] = Field(None, max_length=10)
    InvoiceReference: Optional[str] = Field(None, max_length=100)
    Notes: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    AssetName: Optional[str] = None
    CategoryID: Optional[int] = None
    PurchaseDate: Optional[date] = None
    PurchaseCost: Optional[float] = None
    SalvageValue: Optional[float] = None
    UsefulLifeYears: Optional[int] = None
    DepreciationMethod: Optional[str] = None
    Location: Optional[str] = None
    SerialNumber: Optional[str] = None
    VendorCode: Optional[str] = None
    InvoiceReference: Optional[str] = None
    Status: Optional[str] = None
    Notes: Optional[str] = None


class AssetResponse(AssetBase):
    AssetID: int
    CurrentBookValue: float
    AccumulatedDepreciation: float
    Status: str
    CreatedAt: datetime
    UpdatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssetDetailResponse(AssetResponse):
    category: Optional[AssetCategoryResponse] = None
    depreciation_entries: list["DepreciationResponse"] = []

    class Config:
        from_attributes = True


class DepreciationBase(BaseModel):
    AssetID: int
    PeriodDate: date
    DepreciationAmount: float


class DepreciationCreate(DepreciationBase):
    pass


class DepreciationResponse(DepreciationBase):
    DepreciationID: int
    RunningBookValue: float
    IsPosted: bool
    PostedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class DepreciationScheduleItem(BaseModel):
    PeriodDate: date
    DepreciationAmount: float
    AccumulatedDepreciation: float
    BookValue: float


class DepreciationScheduleResponse(BaseModel):
    AssetID: int
    AssetCode: str
    AssetName: str
    PurchaseCost: float
    SalvageValue: float
    UsefulLifeYears: int
    AnnualDepreciation: float
    MonthlyDepreciation: float
    Schedule: list[DepreciationScheduleItem]


class AssetDisposalBase(BaseModel):
    AssetID: int
    DisposalDate: date
    DisposalType: str = Field(..., max_length=50)
    DisposalProceeds: float = 0
    DisposalCost: float = 0
    Reference: Optional[str] = Field(None, max_length=100)
    Notes: Optional[str] = None


class AssetDisposalCreate(AssetDisposalBase):
    pass


class AssetDisposalResponse(AssetDisposalBase):
    DisposalID: int
    GainLossAmount: float
    BookValueAtDisposal: float
    CreatedAt: datetime

    class Config:
        from_attributes = True


class AssetList(BaseModel):
    items: list[AssetResponse]
    total: int
    page: int = 1
    page_size: int = 50
