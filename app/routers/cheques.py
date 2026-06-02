import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import ChequeCreate, ChequeResponse
from app.models.models import ChequeBook, AuditTrail

router = APIRouter(prefix="/api/v1/cheques", tags=["cheques"])


@router.get("/")
async def list_cheques(status: str = "", bank_account: str = "", limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    q = select(ChequeBook)
    if status: q = q.where(ChequeBook.status == status)
    if bank_account: q = q.where(ChequeBook.bank_account == bank_account)
    q = q.order_by(ChequeBook.id.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return [{"id": r.id, "cheque_no": r.cheque_no, "cheque_date": r.cheque_date, "payee": r.payee, "amount": r.amount, "currency": r.currency, "bank_account": r.bank_account, "status": r.status, "pnr_id": r.pnr_id, "event_id": r.event_id, "cleared_date": r.cleared_date} for r in result.all()]


@router.get("/{cheque_id}", response_model=ChequeResponse)
async def get_cheque(cheque_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    r = await db.get(ChequeBook, cheque_id)
    if not r: raise HTTPException(status_code=404, detail="Cheque not found")
    return r


@router.post("/", response_model=ChequeResponse)
async def create_cheque(data: ChequeCreate, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    r = ChequeBook(**data.model_dump())
    db.add(r); await db.commit(); await db.refresh(r)
    db.add(AuditTrail(table_name="cheque_books", record_id=r.id, action="CREATE", new_values=data.model_dump(), changed_by=user["username"], changed_at=datetime.datetime.utcnow()))
    await db.commit()
    return r


@router.post("/{cheque_id}/status")
async def update_cheque_status(cheque_id: int, status: str, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    r = await db.get(ChequeBook, cheque_id)
    if not r: raise HTTPException(status_code=404, detail="Cheque not found")
    old = {"status": r.status}
    r.status = status
    if status == "cleared": r.cleared_date = datetime.date.today()
    db.add(r)
    db.add(AuditTrail(table_name="cheque_books", record_id=cheque_id, action="STATUS_UPDATE", old_values=old, new_values={"status": status}, changed_by=user["username"], changed_at=datetime.datetime.utcnow()))
    await db.commit(); await db.refresh(r)
    return r


@router.get("/summary/stats")
async def cheque_stats(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    issued = await db.execute(select(func.coalesce(func.sum(ChequeBook.amount), 0)).where(ChequeBook.status == "issued"))
    cleared = await db.execute(select(func.coalesce(func.sum(ChequeBook.amount), 0)).where(ChequeBook.status.in_(["cleared", "cashed"])))
    outstanding = await db.execute(select(func.coalesce(func.sum(ChequeBook.amount), 0)).where(ChequeBook.status == "issued"))
    return {"total_issued": round(float(issued.scalar()), 2), "total_cleared": round(float(cleared.scalar()), 2), "total_outstanding": round(float(outstanding.scalar()), 2)}
