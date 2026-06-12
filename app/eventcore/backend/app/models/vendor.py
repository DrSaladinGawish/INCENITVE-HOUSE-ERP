import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bio_vendor_id = Column(UUID(as_uuid=True))
    name = Column(String(255), nullable=False)
    category = Column(String(50))
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    vat_number = Column(String(50))
    bank_account = Column(String(100))
    bank_name = Column(String(100))
    currency = Column(String(3), default="EGP")
    payment_terms = Column(Integer, default=30)
    rating = Column(Numeric(3, 2))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=_utcnow)
