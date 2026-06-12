import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey, DDL, event
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_code = Column(String(20), unique=True, nullable=False)
    year = Column(Integer, nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    event_name = Column(String(255), nullable=False)
    event_dates = Column(String(50))
    description = Column(Text)

    total_revenue = Column(Numeric(15, 2), default=0)
    total_cost = Column(Numeric(15, 2), default=0)
    gross_profit = Column(Numeric(15, 2), default=0)
    margin_pct = Column(Numeric(5, 2), default=0)

    status = Column(String(20), default="planning")
    margin_target = Column(Numeric(5, 2), default=35.0)

    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
