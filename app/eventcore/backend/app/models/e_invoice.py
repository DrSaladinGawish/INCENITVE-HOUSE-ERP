import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EInvoiceLine(Base):
    __tablename__ = "e_invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_type = Column(String(20), nullable=False)
    sales_invoice_id = Column(UUID(as_uuid=True), ForeignKey("sales_invoices.id"))
    purchase_invoice_id = Column(UUID(as_uuid=True), ForeignKey("purchase_invoices.id"))
    invoice_number = Column(String(100), nullable=False)
    issue_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    vat_amount = Column(Numeric(15, 2), default=0)
    net_amount = Column(Numeric(15, 2), nullable=False)
    eta_status = Column(String(20), default="pending")
    is_synced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
