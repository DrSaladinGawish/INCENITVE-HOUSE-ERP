import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    event_name = Column(String(255), nullable=False)
    event_type = Column(String(50), default="conference")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    destination = Column(String(255))
    venue = Column(String(255))
    pax_count = Column(Integer)
    status = Column(String(20), default="planned")
    cos_account_code = Column(String(20))
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
