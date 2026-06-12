import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=False)
    tax_number = Column(String(50), nullable=False)
    commercial_register = Column(String(50))
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), default="Cairo")
    country = Column(String(100), default="Egypt")
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    logo_url = Column(String(500))
    default_currency = Column(String(3), default="EGP")
    vat_rate = Column(Numeric(5, 2), default=14.0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
