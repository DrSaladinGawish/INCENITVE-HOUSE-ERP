import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import PettyCashCreate, PettyCashResponse
from app.models.models import PettyCashRegister, AuditTrail

router = APIRouter(prefix="/api/v1/petty-cash", tags=["petty-cash"])


@router.get("/")
async def list_petty_cash(
    status: str = "", category: str = "", limit: int = 100, offset: int = 0,
    db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user),
):
    q = select(PettyCashRegister)
    if status: q = q.where(PettyCashRegister.status == status)
    if category: q = q.where(PettyCashRegister.category == category)
    q = q.order_by(PettyCashRegister.id.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    rows = result.all()
    return [{
        "id": r.id, "voucher_no": r.voucher_no, "voucher_date": r.voucher_date,
        "description": r.description, "amount": r.amount, "currency": r.currency,
        "paid_to": r.paid_to, "category": r.category, "pnr_id": r.pnr_id,
        "event_id": r.event_id, "status": r.status, "approved_by": r.approved_by,
    } for r in rows]


@router.get("/{voucher_id}")
async def get_petty_cash(voucher_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    r = await db.get(PettyCashRegister, voucher_id)
    if not r: raise HTTPException(status_code=404, detail="Voucher not found")
    return r


@router.post("/", response_model=PettyCashResponse)
async def create_petty_cash(data: PettyCashCreate, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    r = PettyCashRegister(**data.model_dump())
    db.add(r); await db.commit(); await db.refresh(r)
    db.add(AuditTrail(table_name="petty_cash_register", record_id=r.id, action="CREATE", new_values=data.model_dump(), changed_by=user["username"], changed_at=datetime.datetime.utcnow()))
    await db.commit()
    return r


@router.post("/{voucher_id}/approve")
async def approve_petty_cash(voucher_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    r = await db.get(PettyCashRegister, voucher_id)
    if not r: raise HTTPException(status_code=404, detail="Voucher not found")
    old = {"status": r.status, "approved_by": r.approved_by}
    r.status = "approved"; r.approved_by = user["username"]
    db.add(r)
    db.add(AuditTrail(table_name="petty_cash_register", record_id=voucher_id, action="APPROVE", old_values=old, new_values={"status": "approved", "approved_by": user["username"]}, changed_by=user["username"], changed_at=datetime.datetime.utcnow()))
    await db.commit(); await db.refresh(r)
    return r


@router.get("/summary/stats")
async def petty_cash_stats(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    total = await db.execute(select(func.coalesce(func.sum(PettyCashRegister.amount), 0)).where(PettyCashRegister.status == "approved"))
    pending = await db.execute(select(func.coalesce(func.sum(PettyCashRegister.amount), 0)).where(PettyCashRegister.status == "pending"))
    return {"total_approved": round(float(total.scalar()), 2), "total_pending": round(float(pending.scalar()), 2)}
