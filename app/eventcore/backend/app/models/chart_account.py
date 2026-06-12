import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ChartAccount(Base):
    __tablename__ = "chart_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_code = Column(String(20), unique=True, nullable=False)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(20), nullable=False)
    is_cos = Column(Boolean, default=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
