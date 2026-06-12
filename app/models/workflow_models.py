from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, Date,
    ForeignKey, Numeric, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class WorkflowDefinition(Base):
    __tablename__ = "WorkflowDefinition"
    __table_args__ = {"schema": "dbo"}

    WorkflowID = Column(Integer, primary_key=True, autoincrement=True)
    WorkflowName = Column(String(200), nullable=False)
    Description = Column(Text, nullable=True)
    Module = Column(String(50), nullable=False)
    IsActive = Column(Boolean, default=True)
    CreatedAt = Column(DateTime, default=datetime.utcnow)

    states = relationship("WorkflowState", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowState(Base):
    __tablename__ = "WorkflowState"
    __table_args__ = {"schema": "dbo"}

    StateID = Column(Integer, primary_key=True, autoincrement=True)
    WorkflowID = Column(Integer, ForeignKey("dbo.WorkflowDefinition.WorkflowID"), nullable=False)
    StateName = Column(String(100), nullable=False)
    StateOrder = Column(Integer, nullable=False, default=0)
    RequiredRole = Column(String(50), nullable=True)

    workflow = relationship("WorkflowDefinition", back_populates="states")
    approval_requests = relationship("ApprovalRequest", back_populates="state")


class ApprovalRequest(Base):
    __tablename__ = "ApprovalRequest"
    __table_args__ = {"schema": "dbo"}

    ApprovalID = Column(Integer, primary_key=True, autoincrement=True)
    WorkflowID = Column(Integer, ForeignKey("dbo.WorkflowDefinition.WorkflowID"), nullable=False)
    StateID = Column(Integer, ForeignKey("dbo.WorkflowState.StateID"), nullable=False)
    ReferenceModule = Column(String(50), nullable=False)
    ReferenceID = Column(String(100), nullable=False)
    RequestedBy = Column(String(100), nullable=False)
    RequestedAt = Column(DateTime, default=datetime.utcnow)
    Status = Column(String(20), default="Pending")
    ApprovedBy = Column(String(100), nullable=True)
    ApprovedAt = Column(DateTime, nullable=True)
    Comments = Column(Text, nullable=True)

    workflow = relationship("WorkflowDefinition")
    state = relationship("WorkflowState", back_populates="approval_requests")
    history = relationship("ApprovalHistory", back_populates="approval", cascade="all, delete-orphan")


class ApprovalHistory(Base):
    __tablename__ = "ApprovalHistory"
    __table_args__ = {"schema": "dbo"}

    HistoryID = Column(Integer, primary_key=True, autoincrement=True)
    ApprovalID = Column(Integer, ForeignKey("dbo.ApprovalRequest.ApprovalID"), nullable=False)
    Action = Column(String(20), nullable=False)
    ActionBy = Column(String(100), nullable=False)
    ActionAt = Column(DateTime, default=datetime.utcnow)
    Comments = Column(Text, nullable=True)

    approval = relationship("ApprovalRequest", back_populates="history")
