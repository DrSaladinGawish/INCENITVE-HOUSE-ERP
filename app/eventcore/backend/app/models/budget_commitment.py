import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BudgetCommitment(Base):
    __tablename__ = "budget_commitments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_line_id = Column(UUID(as_uuid=True), ForeignKey("budget_lines.id"), nullable=False)
    purchase_invoice_id = Column(UUID(as_uuid=True), ForeignKey("purchase_invoices.id"))
    sales_invoice_id = Column(UUID(as_uuid=True), ForeignKey("sales_invoices.id"))
    amount = Column(Numeric(15, 2), nullable=False)
    source_type = Column(String(20))
    source_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=_utcnow)
