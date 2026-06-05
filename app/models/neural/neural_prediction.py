from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.database import Base


class NeuralPrediction(Base):
    __tablename__ = "NeuralPrediction"
    __table_args__ = {"schema": "dbo"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, nullable=True)
    organ = Column(String(50), nullable=False)
    cell = Column(String(50), nullable=False)
    prediction_id = Column(String(200), nullable=True)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    actual_outcome = Column(String(500), nullable=True)
    feedback_text = Column(Text, nullable=True)
    feedback_rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
