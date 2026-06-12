from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BudgetPeriod(Base):
    __tablename__ = "BudgetPeriod"
    __table_args__ = {"schema": "dbo"}
    BudgetPeriodCode = Column(String(10), primary_key=True)
    FiscalYear = Column(Integer, nullable=False)
    Quarter = Column(Integer, nullable=True)
    Month = Column(Integer, nullable=True)
    Label = Column(String(100), nullable=False)
    StartDate = Column(Date, nullable=False)
    EndDate = Column(Date, nullable=False)
    IsClosed = Column(Boolean, default=False)
    CreatedAt = Column(DateTime, default=_utcnow)
    UpdatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    lines = relationship("BudgetLine", back_populates="budget_period")


class BudgetLine(Base):
    __tablename__ = "BudgetLine"
    __table_args__ = {"schema": "dbo"}
    BudgetLineID = Column(Integer, primary_key=True, autoincrement=True)
    BudgetPeriodCode = Column(String(10), ForeignKey("dbo.BudgetPeriod.BudgetPeriodCode"), nullable=False)
    AccountCode = Column(String(20), ForeignKey("dbo.ChartOfAccounts.AccountCode"), nullable=True)
    Category = Column(String(50), nullable=False)
    Description = Column(Text, nullable=True)
    BudgetedAmount = Column(Numeric(18, 2), default=0)
    ActualAmount = Column(Numeric(18, 2), default=0)
    CommittedAmount = Column(Numeric(18, 2), default=0)
    Notes = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, default=_utcnow)
    UpdatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    budget_period = relationship("BudgetPeriod", back_populates="lines")
    commitments = relationship("BudgetCommitment", back_populates="budget_line")
    revisions = relationship("BudgetRevision", back_populates="budget_line")


class BudgetCommitment(Base):
    __tablename__ = "BudgetCommitment"
    __table_args__ = {"schema": "dbo"}
    CommitmentID = Column(Integer, primary_key=True, autoincrement=True)
    BudgetLineID = Column(Integer, ForeignKey("dbo.BudgetLine.BudgetLineID"), nullable=False)
    SourceType = Column(String(50), nullable=True)
    SourceID = Column(String(50), nullable=True)
    Amount = Column(Numeric(18, 2), nullable=False)
    CreatedAt = Column(DateTime, default=_utcnow)

    budget_line = relationship("BudgetLine", back_populates="commitments")


class BudgetRevision(Base):
    __tablename__ = "BudgetRevision"
    __table_args__ = {"schema": "dbo"}
    RevisionID = Column(Integer, primary_key=True, autoincrement=True)
    BudgetLineID = Column(Integer, ForeignKey("dbo.BudgetLine.BudgetLineID"), nullable=False)
    PreviousAmount = Column(Numeric(18, 2), nullable=False)
    NewAmount = Column(Numeric(18, 2), nullable=False)
    Reason = Column(Text, nullable=True)
    RevisedBy = Column(String(50), nullable=True)
    RevisedAt = Column(DateTime, default=_utcnow)

    budget_line = relationship("BudgetLine", back_populates="revisions")
