from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Date, Numeric, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AssetCategory(Base):
    __tablename__ = "AssetCategory"
    __table_args__ = {"schema": "dbo"}
    CategoryID = Column(Integer, primary_key=True, autoincrement=True)
    CategoryCode = Column(String(20), nullable=False, unique=True)
    CategoryName = Column(String(200), nullable=False)
    DefaultUsefulLife = Column(Integer, nullable=True)
    DefaultDepreciationRate = Column(Numeric(5, 2), nullable=True)
    GLAssetAccount = Column(String(20), nullable=True)
    GLDepreciationAccount = Column(String(20), nullable=True)
    GLAccumulatedDepAccount = Column(String(20), nullable=True)
    IsActive = Column(Boolean, default=True)

    assets = relationship("Asset", back_populates="category")


class Asset(Base):
    __tablename__ = "Asset"
    __table_args__ = {"schema": "dbo"}
    AssetID = Column(Integer, primary_key=True, autoincrement=True)
    AssetCode = Column(String(50), nullable=False, unique=True)
    AssetName = Column(String(500), nullable=False)
    CategoryID = Column(Integer, ForeignKey("dbo.AssetCategory.CategoryID"), nullable=False)
    PurchaseDate = Column(Date, nullable=False)
    PurchaseCost = Column(Numeric(18, 2), nullable=False)
    SalvageValue = Column(Numeric(18, 2), default=0)
    UsefulLifeYears = Column(Integer, nullable=False)
    DepreciationMethod = Column(String(50), default="StraightLine")
    CurrentBookValue = Column(Numeric(18, 2), nullable=False)
    AccumulatedDepreciation = Column(Numeric(18, 2), default=0)
    Location = Column(String(200), nullable=True)
    SerialNumber = Column(String(100), nullable=True)
    VendorCode = Column(String(10), nullable=True)
    InvoiceReference = Column(String(100), nullable=True)
    Status = Column(String(20), default="Active")
    Notes = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, default=_utcnow)
    UpdatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    category = relationship("AssetCategory", back_populates="assets")
    depreciation_entries = relationship("Depreciation", back_populates="asset", order_by="Depreciation.PeriodDate")
    disposals = relationship("AssetDisposal", back_populates="asset")


class Depreciation(Base):
    __tablename__ = "Depreciation"
    __table_args__ = {"schema": "dbo"}
    DepreciationID = Column(Integer, primary_key=True, autoincrement=True)
    AssetID = Column(Integer, ForeignKey("dbo.Asset.AssetID"), nullable=False)
    PeriodDate = Column(Date, nullable=False)
    DepreciationAmount = Column(Numeric(18, 2), nullable=False)
    RunningBookValue = Column(Numeric(18, 2), nullable=False)
    IsPosted = Column(Boolean, default=False)
    PostedAt = Column(DateTime, nullable=True)
    Notes = Column(Text, nullable=True)

    asset = relationship("Asset", back_populates="depreciation_entries")


class AssetDisposal(Base):
    __tablename__ = "AssetDisposal"
    __table_args__ = {"schema": "dbo"}
    DisposalID = Column(Integer, primary_key=True, autoincrement=True)
    AssetID = Column(Integer, ForeignKey("dbo.Asset.AssetID"), nullable=False)
    DisposalDate = Column(Date, nullable=False)
    DisposalType = Column(String(50), nullable=False)
    DisposalProceeds = Column(Numeric(18, 2), default=0)
    DisposalCost = Column(Numeric(18, 2), default=0)
    GainLossAmount = Column(Numeric(18, 2), nullable=True)
    BookValueAtDisposal = Column(Numeric(18, 2), nullable=False)
    Reference = Column(String(100), nullable=True)
    Notes = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, default=_utcnow)

    asset = relationship("Asset", back_populates="disposals")
