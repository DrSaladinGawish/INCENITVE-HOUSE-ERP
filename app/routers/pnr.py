import json
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.models.models import PNRDim, EventDim, EventPNRAllocation, SalesInvoice, PurchaseInvoice, BankTransaction, AuditTrail, PNRAllocationSummary
from app.schemas import PNRDimCreate, PNRDimUpdate, PNRDimResponse, PNRBulkClassify, PNRAllocationReport
from app.routers.auth import get_current_user, require_role

router = APIRouter(tags=["pnr"])


@router.get("/", response_model=list[PNRDimResponse])
async def list_pnr(
    pnr_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(PNRDim)
    if pnr_type:
        q = q.where(PNRDim.pnr_type == pnr_type)
    if search:
        q = q.where(PNRDim.pnr_code.ilike(f"%{search}%") | PNRDim.name.ilike(f"%{search}%"))
    q = q.offset(offset).limit(limit).order_by(PNRDim.pnr_code)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{pnr_id}", response_model=PNRDimResponse)
async def get_pnr(pnr_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PNRDim).where(PNRDim.pnr_id == pnr_id))
    pnr = result.scalar_one_or_none()
    if not pnr:
        raise HTTPException(status_code=404, detail="PNR not found")
    return pnr


@router.post("/", response_model=PNRDimResponse, status_code=201)
async def create_pnr(
    data: PNRDimCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    existing = await db.execute(select(PNRDim).where(PNRDim.pnr_code == data.pnr_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="PNR code already exists")
    pnr = PNRDim(**data.model_dump())
    db.add(pnr)
    await db.commit()
    await db.refresh(pnr)
    audit = AuditTrail(table_name="pnr_dim", record_id=pnr.pnr_id, action="CREATE", new_values=json.loads(json.dumps(data.model_dump(), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return pnr


@router.put("/{pnr_id}", response_model=PNRDimResponse)
async def update_pnr(
    pnr_id: int,
    data: PNRDimUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    result = await db.execute(select(PNRDim).where(PNRDim.pnr_id == pnr_id))
    pnr = result.scalar_one_or_none()
    if not pnr:
        raise HTTPException(status_code=404, detail="PNR not found")
    old_vals = {c.name: getattr(pnr, c.name) for c in PNRDim.__table__.columns}
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(pnr, k, v)
    pnr.updated_at = datetime.datetime.utcnow()
    await db.commit()
    await db.refresh(pnr)
    audit = AuditTrail(table_name="pnr_dim", record_id=pnr_id, action="UPDATE", old_values=json.loads(json.dumps(old_vals, default=str)), new_values=json.loads(json.dumps(data.model_dump(exclude_unset=True), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return pnr


@router.delete("/{pnr_id}")
async def delete_pnr(
    pnr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    result = await db.execute(select(PNRDim).where(PNRDim.pnr_id == pnr_id))
    pnr = result.scalar_one_or_none()
    if not pnr:
        raise HTTPException(status_code=404, detail="PNR not found")
    pnr.status = "inactive"
    pnr.updated_at = datetime.datetime.utcnow()
    await db.commit()
    audit = AuditTrail(table_name="pnr_dim", record_id=pnr_id, action="DEACTIVATE", new_values={"status": "inactive"}, changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": "PNR deactivated"}


@router.post("/bulk-classify")
async def bulk_classify(
    data: PNRBulkClassify,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    if data.pnr_type not in ("JOB", "ADMIN", "STAFF", "ASSETS", "UNALLOCATED"):
        raise HTTPException(status_code=422, detail="Invalid PNR type")
    updated = 0
    for pid in data.pnr_ids:
        r = await db.execute(select(PNRDim).where(PNRDim.pnr_id == pid))
        p = r.scalar_one_or_none()
        if p:
            p.pnr_type = data.pnr_type
            updated += 1
    await db.commit()
    audit = AuditTrail(table_name="pnr_dim", action="BULK_CLASSIFY", new_values={"pnr_ids": data.pnr_ids, "pnr_type": data.pnr_type}, changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": f"{updated} PNRs classified as {data.pnr_type}"}


@router.get("/report/allocation", response_model=list[PNRAllocationReport])
async def allocation_report(
    pnr_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(PNRDim)
    if pnr_type:
        q = q.where(PNRDim.pnr_type == pnr_type)
    result = await db.execute(q)
    pnrs = result.scalars().all()
    report = []
    for p in pnrs:
        s = await db.execute(select(func.coalesce(func.sum(SalesInvoice.total_amount), 0)).where(SalesInvoice.pnr_id == p.pnr_id))
        s_amt = float(s.scalar())
        s_cnt = (await db.execute(select(func.count(SalesInvoice.inv_id)).where(SalesInvoice.pnr_id == p.pnr_id))).scalar()
        pu = await db.execute(select(func.coalesce(func.sum(PurchaseInvoice.total_amount), 0)).where(PurchaseInvoice.pnr_id == p.pnr_id))
        p_amt = float(pu.scalar())
        p_cnt = (await db.execute(select(func.count(PurchaseInvoice.inv_id)).where(PurchaseInvoice.pnr_id == p.pnr_id))).scalar()
        b = await db.execute(select(func.count(BankTransaction.trnx_id)).where(BankTransaction.pnr_id == p.pnr_id))
        b_cnt = b.scalar()
        report.append(PNRAllocationReport(
            pnr_id=p.pnr_id, pnr_code=p.pnr_code, pnr_type=p.pnr_type or "UNALLOCATED",
            total_debits=s_amt + p_amt, total_credits=0.0, net_balance=s_amt + p_amt,
            sales_count=s_cnt or 0, purchase_count=p_cnt or 0, bank_count=b_cnt or 0,
        ))
    return report


@router.get("/search/fuzzy")
async def fuzzy_search(query: str = Query(min_length=1), db: AsyncSession = Depends(get_db)):
    pattern = f"%{query}%"
    result = await db.execute(
        select(PNRDim).where(or_(PNRDim.pnr_code.ilike(pattern), PNRDim.name.ilike(pattern)))
    )
    return result.scalars().all()
