from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, LargeBinary
from app.database import Base


class NeuralNode(Base):
    __tablename__ = "NeuralNode"
    __table_args__ = {"schema": "dbo"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    organ = Column(String(50), nullable=False, index=True)
    cell = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    model_type = Column(String(50), default="default")
    status = Column(String(20), default="active")
    last_trained = Column(DateTime, nullable=True)
    accuracy = Column(Float, nullable=True)
    training_count = Column(Integer, default=0)
    model_data = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
