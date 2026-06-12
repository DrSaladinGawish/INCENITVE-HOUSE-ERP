import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))

    bank_account = Column(String(100), nullable=False)
    transaction_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    reference = Column(String(255))

    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EGP")

    counterparty = Column(String(255))
    counterparty_account = Column(String(100))

    is_reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime)
    reconciled_by = Column(UUID(as_uuid=True))

    linked_job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    linked_at = Column(DateTime)
    linked_by = Column(UUID(as_uuid=True))
    linked_method = Column(String(20))

    match_confidence = Column(Numeric(5, 2))
    match_reason = Column(Text)

    import_batch_id = Column(UUID(as_uuid=True))
    raw_csv_row = Column(Text)

    created_at = Column(DateTime, default=_utcnow)
