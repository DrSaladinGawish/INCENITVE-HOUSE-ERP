import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class VATReturn(Base):
    __tablename__ = "vat_returns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_sales_vat = Column(Numeric(15, 2), default=0)
    total_purchase_vat = Column(Numeric(15, 2), default=0)
    net_vat_due = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default="draft")
    submitted_at = Column(DateTime)
    submitted_by = Column(UUID(as_uuid=True))
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=_utcnow)
