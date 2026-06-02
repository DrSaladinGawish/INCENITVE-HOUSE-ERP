import json
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.models import SalesInvoice, ClientDim, AuditTrail
from app.schemas import SalesInvoiceCreate, SalesInvoiceResponse
from app.routers.auth import get_current_user, require_role

router = APIRouter(tags=["sales"])


@router.get("/", response_model=list[SalesInvoiceResponse])
async def list_sales_invoices(
    status: Optional[str] = None,
    client_code: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(SalesInvoice)
    if status:
        q = q.where(SalesInvoice.status == status)
    if client_code:
        q = q.where(SalesInvoice.client_code == client_code)
    if category:
        q = q.where(SalesInvoice.category == category)
    q = q.offset(offset).limit(limit).order_by(SalesInvoice.inv_id.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SalesInvoice.category).distinct().where(SalesInvoice.category.isnot(None)))
    cats = result.scalars().all()
    subcats = {}
    for c in cats:
        r = await db.execute(select(SalesInvoice.sub_category).distinct().where(SalesInvoice.category == c))
        subcats[c] = r.scalars().all()
    return {"categories": cats, "sub_categories": subcats}


@router.get("/{inv_id}", response_model=SalesInvoiceResponse)
async def get_sales_invoice(inv_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SalesInvoice).where(SalesInvoice.inv_id == inv_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Sales invoice not found")
    return inv


@router.post("/", response_model=SalesInvoiceResponse, status_code=201)
async def create_sales_invoice(
    data: SalesInvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "accountant")),
):
    existing = await db.execute(select(SalesInvoice).where(SalesInvoice.invoice_no == data.invoice_no))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Invoice number already exists")
    if data.client_code:
        cl = await db.execute(select(ClientDim).where(ClientDim.client_code == data.client_code))
        cli = cl.scalar_one_or_none()
        if cli:
            data.client_id = cli.client_id
    inv = SalesInvoice(**data.model_dump())
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    audit = AuditTrail(table_name="sales_invoices", record_id=inv.inv_id, action="CREATE", new_values=json.loads(json.dumps(data.model_dump(), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return inv


@router.put("/{inv_id}", response_model=SalesInvoiceResponse)
async def update_sales_invoice(
    inv_id: int,
    data: SalesInvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "accountant")),
):
    result = await db.execute(select(SalesInvoice).where(SalesInvoice.inv_id == inv_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Sales invoice not found")
    old_vals = {c.name: getattr(inv, c.name) for c in SalesInvoice.__table__.columns}
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(inv, k, v)
    await db.commit()
    await db.refresh(inv)
    audit = AuditTrail(table_name="sales_invoices", record_id=inv_id, action="UPDATE", old_values=json.loads(json.dumps(old_vals, default=str)), new_values=json.loads(json.dumps(data.model_dump(exclude_unset=True), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return inv


@router.get("/stats/summary")
async def sales_summary(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(func.count(SalesInvoice.inv_id), func.coalesce(func.sum(SalesInvoice.total_amount), 0)))
    cnt, tot = r.one()
    return {"total_invoices": cnt, "total_amount": float(tot)}
