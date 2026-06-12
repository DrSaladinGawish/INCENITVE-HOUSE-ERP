from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=_utcnow, index=True)
    actor_id = Column(String(255), nullable=True)
    actor_name = Column(String(255), nullable=True)
    action = Column(String(50), nullable=False)
    target_type = Column(String(100), nullable=False)
    target_id = Column(String(255), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    description = Column(String(1000), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
