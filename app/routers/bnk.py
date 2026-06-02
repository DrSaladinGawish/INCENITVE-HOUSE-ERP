import json
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.models import BankTransaction, AuditTrail
from app.schemas import BankTransactionCreate, BankTransactionResponse
from app.routers.auth import get_current_user, require_role

router = APIRouter(tags=["bank"])


@router.get("/", response_model=list[BankTransactionResponse])
async def list_bank_transactions(
    trnx_type: Optional[str] = None,
    reconciled: Optional[bool] = None,
    allocation_status: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(BankTransaction)
    if trnx_type:
        q = q.where(BankTransaction.trnx_type == trnx_type)
    if reconciled is not None:
        q = q.where(BankTransaction.reconciled == reconciled)
    if allocation_status:
        q = q.where(BankTransaction.allocation_status == allocation_status)
    q = q.offset(offset).limit(limit).order_by(BankTransaction.trnx_id.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{trnx_id}", response_model=BankTransactionResponse)
async def get_bank_transaction(trnx_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BankTransaction).where(BankTransaction.trnx_id == trnx_id))
    trnx = result.scalar_one_or_none()
    if not trnx:
        raise HTTPException(status_code=404, detail="Bank transaction not found")
    return trnx


@router.post("/", response_model=BankTransactionResponse, status_code=201)
async def create_bank_transaction(
    data: BankTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "accountant")),
):
    trnx = BankTransaction(**data.model_dump())
    db.add(trnx)
    await db.commit()
    await db.refresh(trnx)
    audit = AuditTrail(table_name="bank_transactions", record_id=trnx.trnx_id, action="CREATE", new_values=json.loads(json.dumps(data.model_dump(), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return trnx


@router.post("/{trnx_id}/reconcile")
async def reconcile_transaction(
    trnx_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "accountant")),
):
    result = await db.execute(select(BankTransaction).where(BankTransaction.trnx_id == trnx_id))
    trnx = result.scalar_one_or_none()
    if not trnx:
        raise HTTPException(status_code=404, detail="Bank transaction not found")
    trnx.reconciled = True
    await db.commit()
    audit = AuditTrail(table_name="bank_transactions", record_id=trnx_id, action="RECONCILE", old_values={"reconciled": False}, new_values={"reconciled": True}, changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": "Transaction reconciled", "trnx_id": trnx_id}


@router.post("/reconcile/bulk")
async def bulk_reconcile(
    trnx_ids: list[int],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "accountant")),
):
    for tid in trnx_ids:
        r = await db.execute(select(BankTransaction).where(BankTransaction.trnx_id == tid))
        t = r.scalar_one_or_none()
        if t:
            t.reconciled = True
    await db.commit()
    audit = AuditTrail(table_name="bank_transactions", action="BULK_RECONCILE", new_values={"trnx_ids": trnx_ids}, changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": f"{len(trnx_ids)} transactions reconciled"}


@router.get("/stats/summary")
async def bank_summary(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(func.count(BankTransaction.trnx_id), func.coalesce(func.sum(BankTransaction.credit), 0), func.coalesce(func.sum(BankTransaction.debit), 0)))
    cnt, credit, debit = r.one()
    return {"total_transactions": cnt, "total_credits": float(credit), "total_debits": float(debit), "net": float(credit - debit)}
