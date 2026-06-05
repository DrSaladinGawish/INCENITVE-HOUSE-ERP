from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from app.database import Base


class DocumentModule(Base):
    __tablename__ = "DocumentModule"
    __table_args__ = {"schema": "dbo"}

    ModuleID = Column(Integer, primary_key=True, autoincrement=True)
    ModuleCode = Column(String(50), unique=True, nullable=False, index=True)
    ModuleName = Column(String(200), nullable=False)
    Folder = Column(String(500), nullable=True)
    Description = Column(Text, nullable=True)
    Icon = Column(String(50), nullable=True)
    DisplayOrder = Column(Integer, default=0)
    IsActive = Column(Boolean, default=True)
    CreatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
