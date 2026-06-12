from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate, EventResponse

router = APIRouter(prefix="/api/v1/events", tags=["Events"])


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(payload: EventCreate, db: AsyncSession = Depends(get_db)):
    event = Event(**payload.model_dump())
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


@router.get("", response_model=list[EventResponse])
async def list_events(
    job_id: UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(Event).order_by(Event.start_date.desc())
    if job_id:
        q = q.where(Event.job_id == job_id)
    if status:
        q = q.where(Event.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")
    return event


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(event_id: UUID, payload: EventUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(event, key, val)
    await db.flush()
    await db.refresh(event)
    return event


@router.get("/calendar/upcoming", response_model=list[EventResponse])
async def get_upcoming_events(days: int = Query(30, le=90), db: AsyncSession = Depends(get_db)):
    from datetime import date, timedelta
    today = date.today()
    end = today + timedelta(days=days)
    q = select(Event).where(Event.start_date.between(today, end)).order_by(Event.start_date)
    result = await db.execute(q)
    return result.scalars().all()
