from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, BigInteger
from app.database import Base


class SupportingDocument(Base):
    __tablename__ = "SupportingDocument"
    __table_args__ = {"schema": "dbo"}

    DocumentID = Column(BigInteger, primary_key=True, autoincrement=True)
    FileName = Column(String(500), nullable=False)
    FilePath = Column(String(1000), nullable=True)
    FileSize = Column(BigInteger, nullable=True)
    SHA256 = Column(String(64), nullable=True)
    MimeType = Column(String(100), nullable=True)
    ModuleCode = Column(String(50), nullable=True, index=True)
    LinkedEntityType = Column(String(50), nullable=True, index=True)
    LinkedEntityID = Column(String(100), nullable=True, index=True)
    PNRNumber = Column(String(50), nullable=True, index=True)
    Year = Column(Integer, nullable=True)
    Description = Column(Text, nullable=True)
    Tags = Column(String(500), nullable=True)
    Status = Column(String(20), default="active")
    IsVerified = Column(Boolean, default=False)
    Version = Column(Integer, default=1)
    CreatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    UpdatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
                       onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
