import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import VendorPerformance, VendorDim, AuditTrail

router = APIRouter(prefix="/api/v1/vendor-performance", tags=["vendor-performance"])


@router.get("/{vendor_id}")
async def get_vendor_performance(vendor_id: int, period: str = "", db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    vendor = await db.get(VendorDim, vendor_id)
    if not vendor: raise HTTPException(status_code=404, detail="Vendor not found")
    q = select(VendorPerformance).where(VendorPerformance.vendor_id == vendor_id)
    if period: q = q.where(VendorPerformance.period == period)
    q = q.order_by(VendorPerformance.created_at.desc())
    result = await db.execute(q)
    metrics = {}
    for r in result.all():
        metrics[r.metric_name] = r.metric_value
    return {"vendor_id": vendor_id, "vendor_name": vendor.name, "metrics": metrics, "period": period or "all"}


@router.post("/{vendor_id}/rate")
async def rate_vendor(vendor_id: int, metric_name: str = "quality", metric_value: float = 0.0, period: str = "", db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    vendor = await db.get(VendorDim, vendor_id)
    if not vendor: raise HTTPException(status_code=404, detail="Vendor not found")
    p = period or f"{datetime.date.today().year}-{datetime.date.today().month:02d}"
    r = VendorPerformance(vendor_id=vendor_id, metric_name=metric_name, metric_value=metric_value, period=p)
    db.add(r)
    db.add(AuditTrail(table_name="vendor_performance", record_id=vendor_id, action="RATE", new_values={"metric_name": metric_name, "metric_value": metric_value, "period": p}, changed_by=user["username"], changed_at=datetime.datetime.utcnow()))
    await db.commit(); await db.refresh(r)
    return r


@router.get("/{vendor_id}/summary")
async def vendor_performance_summary(vendor_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    vendor = await db.get(VendorDim, vendor_id)
    if not vendor: raise HTTPException(status_code=404, detail="Vendor not found")
    result = await db.execute(
        select(VendorPerformance.metric_name, func.avg(VendorPerformance.metric_value))
        .where(VendorPerformance.vendor_id == vendor_id)
        .group_by(VendorPerformance.metric_name)
    )
    return {"vendor_id": vendor_id, "vendor_name": vendor.name, "averages": {row[0]: round(float(row[1]), 2) for row in result.all()}}
