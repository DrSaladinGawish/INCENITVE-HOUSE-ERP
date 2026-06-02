import json
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.models.models import EventDim, EventPNRAllocation, PNRDim, AuditTrail, EventCost, EventMilestone
from app.schemas import EventCreate, EventUpdate, EventResponse
from app.routers.auth import get_current_user, require_role

router = APIRouter(tags=["events"])


@router.get("/", response_model=list[EventResponse])
async def list_events(
    status: Optional[str] = None,
    branch: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(EventDim)
    if status:
        q = q.where(EventDim.status == status)
    if branch:
        q = q.where(EventDim.branch == branch)
    if event_type:
        q = q.where(EventDim.event_type == event_type)
    q = q.offset(offset).limit(limit).order_by(EventDim.event_id.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EventDim).where(EventDim.event_id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/", response_model=EventResponse, status_code=201)
async def create_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "event_manager")),
):
    existing = await db.execute(select(EventDim).where(EventDim.event_code == data.event_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Event code already exists")
    event = EventDim(**data.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    audit = AuditTrail(table_name="event_dim", record_id=event.event_id, action="CREATE", new_values=json.loads(json.dumps(data.model_dump(), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "event_manager")),
):
    result = await db.execute(select(EventDim).where(EventDim.event_id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    old_vals = {c.name: getattr(event, c.name) for c in EventDim.__table__.columns}
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(event, k, v)
    event.updated_at = datetime.datetime.utcnow()
    await db.commit()
    await db.refresh(event)
    audit = AuditTrail(table_name="event_dim", record_id=event_id, action="UPDATE", old_values=json.loads(json.dumps(old_vals, default=str)), new_values=json.loads(json.dumps(data.model_dump(exclude_unset=True), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return event


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    result = await db.execute(select(EventDim).where(EventDim.event_id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    old_vals = {c.name: getattr(event, c.name) for c in EventDim.__table__.columns}
    event.status = "cancelled"
    event.updated_at = datetime.datetime.utcnow()
    await db.commit()
    audit = AuditTrail(table_name="event_dim", record_id=event_id, action="DELETE", old_values=json.loads(json.dumps(old_vals, default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": "Event cancelled"}


@router.post("/{event_id}/allocate")
async def allocate_pnr(
    event_id: int,
    pnr_id: int,
    amount: float,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "accountant")),
):
    evt = await db.execute(select(EventDim).where(EventDim.event_id == event_id))
    if not evt.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")
    pnr = await db.execute(select(PNRDim).where(PNRDim.pnr_id == pnr_id))
    if not pnr.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="PNR not found")
    alloc = EventPNRAllocation(event_id=event_id, pnr_id=pnr_id, allocated_amount=amount)
    db.add(alloc)
    await db.commit()
    audit = AuditTrail(table_name="event_pnr_allocation", action="CREATE", new_values={"event_id": event_id, "pnr_id": pnr_id, "amount": amount}, changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": "PNR allocated", "event_id": event_id, "pnr_id": pnr_id, "amount": amount}
