import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.models import ORModuleData, AuditTrail
from app.routers.auth import get_current_user, require_role

router = APIRouter(tags=["operations"])


@router.get("/or-requests")
async def list_or_requests(
    or_type: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(ORModuleData)
    if or_type:
        q = q.where(ORModuleData.or_type == or_type)
    q = q.offset(offset).limit(limit).order_by(ORModuleData.or_id.desc())
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {"or_id": r.or_id, "or_type": r.or_type, "or_number": r.or_number, "or_date": str(r.or_date) if r.or_date else None, "total_amount": r.total_amount, "currency": r.currency, "notes": r.notes}
        for r in rows
    ]


@router.get("/or-requests/{or_id}")
async def get_or_request(or_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ORModuleData).where(ORModuleData.or_id == or_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="OR request not found")
    return {"or_id": row.or_id, "or_type": row.or_type, "or_number": row.or_number, "or_date": str(row.or_date) if row.or_date else None, "total_amount": row.total_amount, "currency": row.currency, "notes": row.notes}


@router.get("/or-requests/stats/summary")
async def or_summary(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(func.count(ORModuleData.or_id), func.coalesce(func.sum(ORModuleData.total_amount), 0)))
    cnt, tot = r.one()
    return {"total_requests": cnt, "total_amount": float(tot)}
