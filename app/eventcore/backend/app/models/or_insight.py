import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Float, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import JSON
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ORInsight(Base):
    __tablename__ = "or_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(50), nullable=False, index=True)
    insight_id = Column(String(100), unique=True, nullable=False)
    module = Column(String(50), nullable=False)
    integration_type = Column(String(50), default="reverse_flow_p2")
    or_score = Column(Float, nullable=True)
    sensitivity_range = Column(JSON, nullable=True)
    status = Column(String(50), nullable=True)
    analysis_url = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    raw_data = Column(JSON, nullable=True)
    ui_render_hints = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    received_at = Column(DateTime, default=_utcnow)
