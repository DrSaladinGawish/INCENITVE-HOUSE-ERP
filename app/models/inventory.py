from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Item(Base):
    __tablename__ = "Item"
    __table_args__ = {"schema": "dbo"}
    ItemID = Column(Integer, primary_key=True, autoincrement=True)
    ItemCode = Column(String(50), nullable=False, unique=True)
    ItemName = Column(String(200), nullable=False)
    SKU = Column(String(100), nullable=True)
    Category = Column(String(100), nullable=True)
    Description = Column(Text, nullable=True)
    UnitPrice = Column(Numeric(18, 2), nullable=True)
    UnitOfMeasure = Column(String(20), nullable=True)
    VATRate = Column(Numeric(5, 2), default=14.00)
    GLAccount = Column(String(20), nullable=True)
    IsActive = Column(Boolean, default=True)
    CreatedAt = Column(DateTime, default=_utcnow)
    UpdatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    stock_movements = relationship("StockMovement", back_populates="item")
    inventory_counts = relationship("InventoryCount", back_populates="item")


class Warehouse(Base):
    __tablename__ = "Warehouse"
    __table_args__ = {"schema": "dbo"}
    WarehouseID = Column(Integer, primary_key=True, autoincrement=True)
    WarehouseCode = Column(String(20), nullable=False, unique=True)
    WarehouseName = Column(String(200), nullable=False)
    Location = Column(String(200), nullable=True)
    IsActive = Column(Boolean, default=True)

    stock_movements = relationship("StockMovement", back_populates="warehouse")
    inventory_counts = relationship("InventoryCount", back_populates="warehouse")


class StockMovement(Base):
    __tablename__ = "StockMovement"
    __table_args__ = {"schema": "dbo"}
    MovementID = Column(Integer, primary_key=True, autoincrement=True)
    ItemID = Column(Integer, ForeignKey("dbo.Item.ItemID"), nullable=False)
    WarehouseID = Column(Integer, ForeignKey("dbo.Warehouse.WarehouseID"), nullable=False)
    MovementType = Column(String(20), nullable=False)
    Quantity = Column(Numeric(18, 2), nullable=False)
    UnitPrice = Column(Numeric(18, 2), nullable=True)
    TotalValue = Column(Numeric(18, 2), nullable=True)
    Reference = Column(String(100), nullable=True)
    ReferenceType = Column(String(50), nullable=True)
    Narration = Column(Text, nullable=True)
    MovementDate = Column(DateTime, default=_utcnow)
    CreatedBy = Column(String(50), nullable=True)
    CreatedAt = Column(DateTime, default=_utcnow)

    item = relationship("Item", back_populates="stock_movements")
    warehouse = relationship("Warehouse", back_populates="stock_movements")


class InventoryCount(Base):
    __tablename__ = "InventoryCount"
    __table_args__ = {"schema": "dbo"}
    CountID = Column(Integer, primary_key=True, autoincrement=True)
    ItemID = Column(Integer, ForeignKey("dbo.Item.ItemID"), nullable=False)
    WarehouseID = Column(Integer, ForeignKey("dbo.Warehouse.WarehouseID"), nullable=False)
    ExpectedQuantity = Column(Numeric(18, 2), nullable=True)
    ActualQuantity = Column(Numeric(18, 2), nullable=False)
    Variance = Column(Numeric(18, 2), nullable=True)
    CountDate = Column(DateTime, default=_utcnow)
    CountedBy = Column(String(50), nullable=True)
    Remarks = Column(Text, nullable=True)
    IsAdjusted = Column(Boolean, default=False)
    CreatedAt = Column(DateTime, default=_utcnow)

    item = relationship("Item", back_populates="inventory_counts")
    warehouse = relationship("Warehouse", back_populates="inventory_counts")
