from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from app.database import Base


class NeuralMemory(Base):
    __tablename__ = "NeuralMemory"
    __table_args__ = {"schema": "dbo"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_key = Column(String(200), nullable=False, unique=True, index=True)
    memory_type = Column(String(50), default="insight")
    organ = Column(String(50), nullable=True)
    cell = Column(String(50), nullable=True)
    content = Column(Text, nullable=True)
    importance = Column(Float, default=0.5)
    access_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_accessed_at = Column(DateTime, nullable=True)
