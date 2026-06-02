import json
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.models import ClientDim, EventDim, SalesInvoice, AuditTrail
from app.schemas import ClientCreate, ClientUpdate, ClientResponse
from app.routers.auth import get_current_user, require_role

router = APIRouter(tags=["clients"])


@router.get("/", response_model=list[ClientResponse])
async def list_clients(
    search: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(ClientDim).where(ClientDim.is_deleted == False)
    if category:
        q = q.where(ClientDim.category == category)
    if search:
        q = q.where(ClientDim.name.ilike(f"%{search}%") | ClientDim.client_code.ilike(f"%{search}%"))
    q = q.offset(offset).limit(limit).order_by(ClientDim.name)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClientDim).where(ClientDim.client_id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(
    data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    existing = await db.execute(select(ClientDim).where(ClientDim.client_code == data.client_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Client code already exists")
    client = ClientDim(**data.model_dump())
    db.add(client)
    await db.commit()
    await db.refresh(client)
    audit = AuditTrail(table_name="client_dim", record_id=client.client_id, action="CREATE", new_values=json.loads(json.dumps(data.model_dump(), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    result = await db.execute(select(ClientDim).where(ClientDim.client_id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    old_vals = {c.name: getattr(client, c.name) for c in ClientDim.__table__.columns}
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(client, k, v)
    client.updated_at = datetime.datetime.utcnow()
    await db.commit()
    await db.refresh(client)
    audit = AuditTrail(table_name="client_dim", record_id=client_id, action="UPDATE", old_values=json.loads(json.dumps(old_vals, default=str)), new_values=json.loads(json.dumps(data.model_dump(exclude_unset=True), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return client


@router.delete("/{client_id}")
async def soft_delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    result = await db.execute(select(ClientDim).where(ClientDim.client_id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.is_deleted = True
    client.updated_at = datetime.datetime.utcnow()
    await db.commit()
    audit = AuditTrail(table_name="client_dim", record_id=client_id, action="SOFT_DELETE", old_values={"is_deleted": False}, new_values={"is_deleted": True}, changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": "Client soft deleted"}


@router.get("/{client_id}/events")
async def get_client_events(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClientDim).where(ClientDim.client_id == client_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Client not found")
    evts = await db.execute(select(EventDim).where(EventDim.event_id == client_id).order_by(EventDim.start_date.desc()))
    return [{"event_id": e.event_id, "event_code": e.event_code, "name": e.name, "start_date": str(e.start_date) if e.start_date else None, "status": e.status, "revenue": e.revenue} for e in evts.scalars().all()]


@router.get("/{client_id}/invoices")
async def get_client_invoices(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClientDim).where(ClientDim.client_id == client_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Client not found")
    invs = await db.execute(select(SalesInvoice).where(SalesInvoice.client_id == client_id).order_by(SalesInvoice.invoice_date.desc()))
    return [{"inv_id": i.inv_id, "invoice_no": i.invoice_no, "invoice_date": str(i.invoice_date) if i.invoice_date else None, "total_amount": i.total_amount, "status": i.status} for i in invs.scalars().all()]
