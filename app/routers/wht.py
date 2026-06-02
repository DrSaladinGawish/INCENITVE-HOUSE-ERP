import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import WHTRecordCreate, WHTRecordResponse
from app.models.models import WHTRecord, AuditTrail

router = APIRouter(prefix="/api/v1/wht", tags=["wht"])


@router.get("/")
async def list_wht(status: str = "", period: str = "", limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    q = select(WHTRecord)
    if status: q = q.where(WHTRecord.status == status)
    if period: q = q.where(WHTRecord.period == period)
    q = q.order_by(WHTRecord.id.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return [{
        "id": r.id, "certificate_no": r.certificate_no, "deduction_date": r.deduction_date,
        "vendor_id": r.vendor_id, "gross_amount": r.gross_amount, "wht_rate": r.wht_rate,
        "wht_amount": r.wht_amount, "invoice_ref": r.invoice_ref, "period": r.period,
        "status": r.status, "filed_at": r.filed_at,
    } for r in result.all()]


@router.get("/{wht_id}", response_model=WHTRecordResponse)
async def get_wht(wht_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    r = await db.get(WHTRecord, wht_id)
    if not r: raise HTTPException(status_code=404, detail="WHT record not found")
    return r


@router.post("/", response_model=WHTRecordResponse)
async def create_wht(data: WHTRecordCreate, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    wht_amount = round(data.gross_amount * data.wht_rate / 100, 2)
    r = WHTRecord(certificate_no=data.certificate_no, deduction_date=data.deduction_date, vendor_id=data.vendor_id, gross_amount=data.gross_amount, wht_rate=data.wht_rate, wht_amount=wht_amount, invoice_ref=data.invoice_ref, period=data.period, notes=data.notes)
    db.add(r); await db.commit(); await db.refresh(r)
    db.add(AuditTrail(table_name="wht_records", record_id=r.id, action="CREATE", new_values={"certificate_no": data.certificate_no, "gross_amount": data.gross_amount, "wht_amount": wht_amount}, changed_by=user["username"], changed_at=datetime.datetime.utcnow()))
    await db.commit()
    return r


@router.post("/{wht_id}/file")
async def file_wht(wht_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    r = await db.get(WHTRecord, wht_id)
    if not r: raise HTTPException(status_code=404, detail="WHT record not found")
    old = {"status": r.status}
    r.status = "filed"; r.filed_at = datetime.date.today()
    db.add(r)
    db.add(AuditTrail(table_name="wht_records", record_id=wht_id, action="FILE", old_values=old, new_values={"status": "filed", "filed_at": str(r.filed_at)}, changed_by=user["username"], changed_at=datetime.datetime.utcnow()))
    await db.commit(); await db.refresh(r)
    return r


@router.get("/summary/stats")
async def wht_stats(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    total = await db.execute(select(func.coalesce(func.sum(WHTRecord.wht_amount), 0)))
    pending = await db.execute(select(func.coalesce(func.sum(WHTRecord.wht_amount), 0)).where(WHTRecord.status == "pending"))
    return {"total_wht": round(float(total.scalar()), 2), "pending_wht": round(float(pending.scalar()), 2)}
