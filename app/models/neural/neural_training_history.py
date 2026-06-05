from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from app.database import Base


class NeuralTrainingHistory(Base):
    __tablename__ = "NeuralTrainingHistory"
    __table_args__ = {"schema": "dbo"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, nullable=False, index=True)
    training_date = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    samples = Column(Integer, default=0)
    features = Column(Integer, default=0)
    accuracy = Column(Float, nullable=True)
    loss = Column(Float, nullable=True)
    status = Column(String(20), default="pending")
    model_data = Column(LargeBinary, nullable=True)
    metrics_json = Column(String(2000), nullable=True)
    duration_seconds = Column(Float, nullable=True)
