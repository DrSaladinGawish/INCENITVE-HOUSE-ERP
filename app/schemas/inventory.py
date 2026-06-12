from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    ItemCode: str = Field(..., max_length=50)
    ItemName: str = Field(..., max_length=200)
    SKU: Optional[str] = Field(None, max_length=100)
    Category: Optional[str] = Field(None, max_length=100)
    Description: Optional[str] = None
    UnitPrice: Optional[float] = None
    UnitOfMeasure: Optional[str] = Field(None, max_length=20)
    VATRate: Optional[float] = 14.00
    GLAccount: Optional[str] = Field(None, max_length=20)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    ItemName: Optional[str] = None
    SKU: Optional[str] = None
    Category: Optional[str] = None
    Description: Optional[str] = None
    UnitPrice: Optional[float] = None
    UnitOfMeasure: Optional[str] = None
    VATRate: Optional[float] = None
    GLAccount: Optional[str] = None
    IsActive: Optional[bool] = None


class ItemResponse(ItemBase):
    ItemID: int
    IsActive: bool
    CreatedAt: Optional[datetime] = None
    UpdatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class WarehouseBase(BaseModel):
    WarehouseCode: str = Field(..., max_length=20)
    WarehouseName: str = Field(..., max_length=200)
    Location: Optional[str] = Field(None, max_length=200)


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    WarehouseName: Optional[str] = None
    Location: Optional[str] = None
    IsActive: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    WarehouseID: int
    IsActive: bool

    class Config:
        from_attributes = True


class StockMovementBase(BaseModel):
    ItemID: int
    WarehouseID: int
    MovementType: str = Field(..., max_length=20)
    Quantity: float
    UnitPrice: Optional[float] = None
    Reference: Optional[str] = Field(None, max_length=100)
    ReferenceType: Optional[str] = Field(None, max_length=50)
    Narration: Optional[str] = None


class StockMovementCreate(StockMovementBase):
    pass


class StockMovementResponse(StockMovementBase):
    MovementID: int
    TotalValue: Optional[float] = None
    MovementDate: Optional[datetime] = None
    CreatedBy: Optional[str] = None
    CreatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True


class InventoryCountBase(BaseModel):
    ItemID: int
    WarehouseID: int
    ActualQuantity: float
    CountedBy: Optional[str] = Field(None, max_length=50)
    Remarks: Optional[str] = None


class InventoryCountCreate(InventoryCountBase):
    pass


class InventoryCountResponse(InventoryCountBase):
    CountID: int
    ExpectedQuantity: Optional[float] = None
    Variance: Optional[float] = None
    CountDate: Optional[datetime] = None
    IsAdjusted: bool

    class Config:
        from_attributes = True
