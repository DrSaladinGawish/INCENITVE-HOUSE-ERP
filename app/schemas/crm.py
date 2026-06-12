from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class LeadBase(BaseModel):
    CompanyName: str = Field(..., max_length=200)
    ContactName: Optional[str] = Field(None, max_length=200)
    Email: Optional[str] = Field(None, max_length=200)
    Phone: Optional[str] = Field(None, max_length=50)
    Mobile: Optional[str] = Field(None, max_length=50)
    Source: Optional[str] = Field(None, max_length=50)
    Industry: Optional[str] = Field(None, max_length=100)
    Status: str = Field("New", max_length=20)
    Rating: int = 0
    Description: Optional[str] = None
    AssignedTo: Optional[str] = Field(None, max_length=100)


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    CompanyName: Optional[str] = None
    ContactName: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None
    Mobile: Optional[str] = None
    Source: Optional[str] = None
    Industry: Optional[str] = None
    Status: Optional[str] = None
    Rating: Optional[int] = None
    Description: Optional[str] = None
    AssignedTo: Optional[str] = None


class LeadResponse(LeadBase):
    LeadID: int
    ConvertedToOpportunity: bool
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True


class LeadList(BaseModel):
    items: list[LeadResponse]
    total: int
    page: int = 1
    page_size: int = 50


class OpportunityBase(BaseModel):
    LeadID: Optional[int] = None
    OpportunityName: str = Field(..., max_length=300)
    ClientCode: Optional[str] = Field(None, max_length=10)
    PNRNumber: Optional[str] = Field(None, max_length=50)
    Stage: str = Field("Prospecting", max_length=30)
    Amount: Optional[float] = None
    CurrencyCode: str = Field("EGP", max_length=3)
    Probability: int = 0
    CloseDate: Optional[date] = None
    Description: Optional[str] = None
    AssignedTo: Optional[str] = Field(None, max_length=100)


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    OpportunityName: Optional[str] = None
    ClientCode: Optional[str] = None
    PNRNumber: Optional[str] = None
    Stage: Optional[str] = None
    Amount: Optional[float] = None
    CurrencyCode: Optional[str] = None
    Probability: Optional[int] = None
    CloseDate: Optional[date] = None
    Description: Optional[str] = None
    AssignedTo: Optional[str] = None


class OpportunityResponse(OpportunityBase):
    OpportunityID: int
    WonAt: Optional[datetime] = None
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True


class ContactBase(BaseModel):
    ClientCode: Optional[str] = Field(None, max_length=10)
    FirstName: str = Field(..., max_length=100)
    LastName: str = Field(..., max_length=100)
    Email: Optional[str] = Field(None, max_length=200)
    Phone: Optional[str] = Field(None, max_length=50)
    Mobile: Optional[str] = Field(None, max_length=50)
    JobTitle: Optional[str] = Field(None, max_length=100)
    Department: Optional[str] = Field(None, max_length=100)
    IsPrimary: bool = False
    Notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    FirstName: Optional[str] = None
    LastName: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None
    Mobile: Optional[str] = None
    JobTitle: Optional[str] = None
    Department: Optional[str] = None
    IsPrimary: Optional[bool] = None
    Notes: Optional[str] = None


class ContactResponse(ContactBase):
    ContactID: int
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True


class ActivityBase(BaseModel):
    OpportunityID: Optional[int] = None
    ActivityType: str = Field(..., max_length=30)
    Subject: str = Field(..., max_length=300)
    Description: Optional[str] = None
    ActivityDate: Optional[date] = None
    DueDate: Optional[date] = None
    Status: str = Field("Open", max_length=20)
    Priority: str = Field("Normal", max_length=10)
    AssignedTo: Optional[str] = Field(None, max_length=100)


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    ActivityType: Optional[str] = None
    Subject: Optional[str] = None
    Description: Optional[str] = None
    ActivityDate: Optional[date] = None
    DueDate: Optional[date] = None
    Status: Optional[str] = None
    Priority: Optional[str] = None
    AssignedTo: Optional[str] = None


class ActivityResponse(ActivityBase):
    ActivityID: int
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True


class DealBase(BaseModel):
    OpportunityID: Optional[int] = None
    DealName: str = Field(..., max_length=300)
    ClientCode: Optional[str] = Field(None, max_length=10)
    Amount: Optional[float] = None
    CurrencyCode: str = Field("EGP", max_length=3)
    Stage: str = Field("Negotiation", max_length=30)
    Status: str = Field("Open", max_length=20)
    ExpectedCloseDate: Optional[date] = None
    ActualCloseDate: Optional[date] = None
    Description: Optional[str] = None
    AssignedTo: Optional[str] = Field(None, max_length=100)


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    DealName: Optional[str] = None
    ClientCode: Optional[str] = None
    Amount: Optional[float] = None
    CurrencyCode: Optional[str] = None
    Stage: Optional[str] = None
    Status: Optional[str] = None
    ExpectedCloseDate: Optional[date] = None
    ActualCloseDate: Optional[date] = None
    Description: Optional[str] = None
    AssignedTo: Optional[str] = None


class DealResponse(DealBase):
    DealID: int
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True
