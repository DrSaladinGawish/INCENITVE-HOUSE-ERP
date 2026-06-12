import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))

    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"))
    vendor_name = Column(String(255), nullable=False)

    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)

    subtotal = Column(Numeric(15, 2), nullable=False)
    vat_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EGP")
    exchange_rate = Column(Numeric(10, 6), default=1)

    eta_doc_id = Column(String(100))
    eta_csv_row = Column(Integer)
    eta_imported_at = Column(DateTime)

    status = Column(String(20), default="pending")
    payment_status = Column(String(20), default="unpaid")

    pdf_path = Column(String(500))
    payment_voucher_id = Column(UUID(as_uuid=True))

    linked_by = Column(UUID(as_uuid=True))
    linked_at = Column(DateTime, default=_utcnow)
    linked_method = Column(String(20), default="manual")

    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
