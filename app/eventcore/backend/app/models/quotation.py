import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)

    quote_number = Column(String(50), unique=True, nullable=False)
    quote_date = Column(Date, nullable=False)
    valid_until = Column(Date)

    event_name = Column(String(255), nullable=False)
    event_dates = Column(String(50))
    destination = Column(String(255))
    pax_count = Column(Integer)

    subtotal = Column(Numeric(15, 2), default=0)
    vat_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="EGP")

    status = Column(String(20), default="draft")
    converted_to_job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    converted_at = Column(DateTime)

    pdf_path = Column(String(500))

    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class QuotationLineItem(Base):
    __tablename__ = "quotation_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False)

    category = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    vendor_estimate = Column(String(255))
    notes = Column(Text)
    sort_order = Column(Integer, default=0)
