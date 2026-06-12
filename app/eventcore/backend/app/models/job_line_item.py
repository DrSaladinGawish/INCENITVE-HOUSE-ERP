import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class JobLineItem(Base):
    __tablename__ = "job_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)

    type = Column(String(10), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    sub_category = Column(String(100))
    quantity = Column(Numeric(10, 2), default=1)
    unit_price = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EGP")

    source_type = Column(String(50))
    source_id = Column(UUID(as_uuid=True))

    vendor_id = Column(UUID(as_uuid=True))
    client_invoice_id = Column(UUID(as_uuid=True))

    is_committed = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)

    created_at = Column(DateTime, default=_utcnow)
