import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SalesInvoice(Base):
    __tablename__ = "sales_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)

    eta_doc_id = Column(String(100))
    eta_csv_row = Column(Integer)
    eta_imported_at = Column(DateTime)

    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)

    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    client_vat = Column(String(50))

    subtotal = Column(Numeric(15, 2), nullable=False)
    vat_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EGP")

    eta_prod_name = Column(String(255))

    status = Column(String(20), default="draft")
    payment_status = Column(String(20), default="unpaid")

    collected_amount = Column(Numeric(15, 2), default=0)
    collected_date = Column(Date)

    created_at = Column(DateTime, default=_utcnow)

    line_items = relationship("SalesInvoiceLineItem", backref="invoice", cascade="all, delete-orphan",
                              order_by="SalesInvoiceLineItem.sort_order")


class SalesInvoiceLineItem(Base):
    __tablename__ = "sales_invoice_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("sales_invoices.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit_price = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    sort_order = Column(Integer, default=0)
