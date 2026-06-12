import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, Text, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class JournalVoucher(Base):
    __tablename__ = "journal_vouchers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voucher_number = Column(String(50), unique=True, nullable=False)
    voucher_date = Column(Date, nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    description = Column(Text)
    debit_account = Column(String(50), nullable=False)
    credit_account = Column(String(50), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EGP")
    status = Column(String(20), default="draft")
    posted_by = Column(UUID(as_uuid=True))
    posted_at = Column(DateTime)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=_utcnow)
