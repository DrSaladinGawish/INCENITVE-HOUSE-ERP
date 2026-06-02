import json
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.models import VendorDim, PurchaseInvoice, AuditTrail
from app.schemas import VendorCreate, VendorUpdate, VendorResponse
from app.routers.auth import get_current_user, require_role

router = APIRouter(tags=["vendors"])


@router.get("/", response_model=list[VendorResponse])
async def list_vendors(
    search: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(VendorDim).where(VendorDim.is_deleted == False)
    if category:
        q = q.where(VendorDim.category == category)
    if search:
        q = q.where(VendorDim.name.ilike(f"%{search}%") | VendorDim.vendor_code.ilike(f"%{search}%"))
    q = q.offset(offset).limit(limit).order_by(VendorDim.name)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VendorDim).where(VendorDim.vendor_id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.post("/", response_model=VendorResponse, status_code=201)
async def create_vendor(
    data: VendorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    existing = await db.execute(select(VendorDim).where(VendorDim.vendor_code == data.vendor_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Vendor code already exists")
    vendor = VendorDim(**data.model_dump())
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    audit = AuditTrail(table_name="vendor_dim", record_id=vendor.vendor_id, action="CREATE", new_values=json.loads(json.dumps(data.model_dump(), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return vendor


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: int,
    data: VendorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    result = await db.execute(select(VendorDim).where(VendorDim.vendor_id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    old_vals = {c.name: getattr(vendor, c.name) for c in VendorDim.__table__.columns}
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(vendor, k, v)
    vendor.updated_at = datetime.datetime.utcnow()
    await db.commit()
    await db.refresh(vendor)
    audit = AuditTrail(table_name="vendor_dim", record_id=vendor_id, action="UPDATE", old_values=json.loads(json.dumps(old_vals, default=str)), new_values=json.loads(json.dumps(data.model_dump(exclude_unset=True), default=str)), changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return vendor


@router.delete("/{vendor_id}")
async def soft_delete_vendor(
    vendor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    result = await db.execute(select(VendorDim).where(VendorDim.vendor_id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.is_deleted = True
    vendor.updated_at = datetime.datetime.utcnow()
    await db.commit()
    audit = AuditTrail(table_name="vendor_dim", record_id=vendor_id, action="SOFT_DELETE", old_values={"is_deleted": False}, new_values={"is_deleted": True}, changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": "Vendor soft deleted"}


@router.get("/{vendor_id}/purchase-invoices")
async def get_vendor_purchase_invoices(vendor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VendorDim).where(VendorDim.vendor_id == vendor_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Vendor not found")
    invs = await db.execute(select(PurchaseInvoice).where(PurchaseInvoice.vendor_id == vendor_id).order_by(PurchaseInvoice.invoice_date.desc()))
    return [{"inv_id": i.inv_id, "invoice_no": i.invoice_no, "invoice_date": str(i.invoice_date) if i.invoice_date else None, "total_amount": i.total_amount, "status": i.status} for i in invs.scalars().all()]


@router.get("/{vendor_id}/performance")
async def get_vendor_performance(vendor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VendorDim).where(VendorDim.vendor_id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    pos = await db.execute(select(PurchaseInvoice).where(PurchaseInvoice.vendor_id == vendor_id))
    invoices = pos.scalars().all()
    total = len(invoices)
    on_time = sum(1 for i in invoices if i.status in ("approved", "paid"))
    return {
        "vendor_id": vendor_id,
        "vendor_name": vendor.name,
        "total_purchase_invoices": total,
        "total_spend": sum(i.total_amount for i in invoices),
        "on_time_pct": round((on_time / total * 100), 2) if total else 0,
    }
