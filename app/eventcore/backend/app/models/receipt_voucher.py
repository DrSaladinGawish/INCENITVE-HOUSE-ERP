import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ReceiptVoucher(Base):
    __tablename__ = "receipt_vouchers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voucher_number = Column(String(50), unique=True, nullable=False)

    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"))
    sales_invoice_id = Column(UUID(as_uuid=True), ForeignKey("sales_invoices.id"))

    receipt_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EGP")
    payment_method = Column(String(20))
    bank_account = Column(String(100))

    status = Column(String(20), default="pending")

    received_by = Column(UUID(as_uuid=True))
    received_at = Column(DateTime)

    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=_utcnow)
