from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class EventCreate(BaseModel):
    job_id: UUID
    event_name: str
    event_type: str = "conference"
    start_date: date
    end_date: Optional[date] = None
    destination: Optional[str] = None
    venue: Optional[str] = None
    pax_count: Optional[int] = None
    status: str = "planned"


class EventUpdate(BaseModel):
    event_name: Optional[str] = None
    event_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    destination: Optional[str] = None
    venue: Optional[str] = None
    pax_count: Optional[int] = None
    status: Optional[str] = None


class EventResponse(BaseModel):
    id: UUID
    job_id: UUID
    event_name: str
    event_type: str
    start_date: date
    end_date: Optional[date] = None
    destination: Optional[str] = None
    venue: Optional[str] = None
    pax_count: Optional[int] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
