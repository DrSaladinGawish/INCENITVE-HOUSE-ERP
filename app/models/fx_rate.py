from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, Index
from app.database import Base


class FxRate(Base):
    __tablename__ = "FxRate"
    __table_args__ = (
        Index("ix_fxrate_date_currency", "RateDate", "FromCurrency", "ToCurrency", unique=True),
        {"schema": "dbo"},
    )

    RateID = Column(Integer, primary_key=True, autoincrement=True)
    RateDate = Column(Date, nullable=False)
    FromCurrency = Column(String(3), nullable=False)
    ToCurrency = Column(String(3), nullable=False)
    Rate = Column(Numeric(18, 6), nullable=False)
    Source = Column(String(20), default="manual")
    CreatedAt = Column(DateTime, default=datetime.utcnow)
