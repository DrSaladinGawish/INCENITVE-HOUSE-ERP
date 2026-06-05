from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.database import Base


class NeuralFeatureStore(Base):
    __tablename__ = "NeuralFeatureStore"
    __table_args__ = {"schema": "dbo"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    feature_group = Column(String(100), nullable=False, index=True)
    feature_name = Column(String(200), nullable=False)
    feature_value = Column(Float, nullable=True)
    feature_json = Column(Text, nullable=True)
    entity_id = Column(String(100), nullable=True)
    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at = Column(DateTime, nullable=True)
