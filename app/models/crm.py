from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Date, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Lead(Base):
    __tablename__ = "CRM_Lead"
    __table_args__ = {"schema": "dbo"}
    LeadID = Column(Integer, primary_key=True, autoincrement=True)
    CompanyName = Column(String(200), nullable=False)
    ContactName = Column(String(200), nullable=True)
    Email = Column(String(200), nullable=True)
    Phone = Column(String(50), nullable=True)
    Mobile = Column(String(50), nullable=True)
    Source = Column(String(50), nullable=True)
    Industry = Column(String(100), nullable=True)
    Status = Column(String(20), default="New")
    Rating = Column(Integer, default=0)
    Description = Column(Text, nullable=True)
    AssignedTo = Column(String(100), nullable=True)
    CreatedAt = Column(DateTime, default=_utcnow)
    UpdatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    ConvertedToOpportunity = Column(Boolean, default=False)

    opportunities = relationship("Opportunity", back_populates="lead")


class Opportunity(Base):
    __tablename__ = "CRM_Opportunity"
    __table_args__ = {"schema": "dbo"}
    OpportunityID = Column(Integer, primary_key=True, autoincrement=True)
    LeadID = Column(Integer, ForeignKey("dbo.CRM_Lead.LeadID"), nullable=True)
    OpportunityName = Column(String(300), nullable=False)
    ClientCode = Column(String(10), nullable=True)
    PNRNumber = Column(String(50), nullable=True)
    Stage = Column(String(30), default="Prospecting")
    Amount = Column(Numeric(18, 2), default=0)
    CurrencyCode = Column(String(3), default="EGP")
    Probability = Column(Integer, default=0)
    CloseDate = Column(Date, nullable=True)
    Description = Column(Text, nullable=True)
    AssignedTo = Column(String(100), nullable=True)
    CreatedAt = Column(DateTime, default=_utcnow)
    UpdatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    WonAt = Column(DateTime, nullable=True)

    lead = relationship("Lead", back_populates="opportunities")
    activities = relationship("Activity", back_populates="opportunity")
    deals = relationship("Deal", back_populates="opportunity")


class Contact(Base):
    __tablename__ = "CRM_Contact"
    __table_args__ = {"schema": "dbo"}
    ContactID = Column(Integer, primary_key=True, autoincrement=True)
    ClientCode = Column(String(10), nullable=True)
    FirstName = Column(String(100), nullable=False)
    LastName = Column(String(100), nullable=False)
    Email = Column(String(200), nullable=True)
    Phone = Column(String(50), nullable=True)
    Mobile = Column(String(50), nullable=True)
    JobTitle = Column(String(100), nullable=True)
    Department = Column(String(100), nullable=True)
    IsPrimary = Column(Boolean, default=False)
    Notes = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, default=_utcnow)
    UpdatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class Activity(Base):
    __tablename__ = "CRM_Activity"
    __table_args__ = {"schema": "dbo"}
    ActivityID = Column(Integer, primary_key=True, autoincrement=True)
    OpportunityID = Column(Integer, ForeignKey("dbo.CRM_Opportunity.OpportunityID"), nullable=True)
    ActivityType = Column(String(30), nullable=False)
    Subject = Column(String(300), nullable=False)
    Description = Column(Text, nullable=True)
    ActivityDate = Column(Date, nullable=True)
    DueDate = Column(Date, nullable=True)
    Status = Column(String(20), default="Open")
    Priority = Column(String(10), default="Normal")
    AssignedTo = Column(String(100), nullable=True)
    CreatedAt = Column(DateTime, default=_utcnow)
    UpdatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    opportunity = relationship("Opportunity", back_populates="activities")


class Deal(Base):
    __tablename__ = "CRM_Deal"
    __table_args__ = {"schema": "dbo"}
    DealID = Column(Integer, primary_key=True, autoincrement=True)
    OpportunityID = Column(Integer, ForeignKey("dbo.CRM_Opportunity.OpportunityID"), nullable=True)
    DealName = Column(String(300), nullable=False)
    ClientCode = Column(String(10), nullable=True)
    Amount = Column(Numeric(18, 2), default=0)
    CurrencyCode = Column(String(3), default="EGP")
    Stage = Column(String(30), default="Negotiation")
    Status = Column(String(20), default="Open")
    ExpectedCloseDate = Column(Date, nullable=True)
    ActualCloseDate = Column(Date, nullable=True)
    Description = Column(Text, nullable=True)
    AssignedTo = Column(String(100), nullable=True)
    CreatedAt = Column(DateTime, default=_utcnow)
    UpdatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    opportunity = relationship("Opportunity", back_populates="deals")
