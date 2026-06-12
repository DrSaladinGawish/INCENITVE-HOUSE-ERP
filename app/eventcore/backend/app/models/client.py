import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_code = Column(String(10), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    industry = Column(String(100))
    vat_number = Column(String(50))
    default_currency = Column(String(3), default="EGP")
    credit_limit = Column(Numeric(15, 2), default=0)
    payment_terms = Column(Integer, default=30)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
