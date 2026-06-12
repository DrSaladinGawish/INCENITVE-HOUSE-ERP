import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PettyCash(Base):
    __tablename__ = "petty_cash"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)

    staff_id = Column(UUID(as_uuid=True))
    staff_name = Column(String(255), nullable=False)

    expense_date = Column(Date, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EGP")

    has_receipt = Column(Boolean, default=False)
    receipt_path = Column(String(500))

    status = Column(String(20), default="pending")
    approved_by = Column(UUID(as_uuid=True))
    approved_at = Column(DateTime)

    reimbursed_at = Column(DateTime)
    reimbursement_method = Column(String(20))

    created_at = Column(DateTime, default=_utcnow)
