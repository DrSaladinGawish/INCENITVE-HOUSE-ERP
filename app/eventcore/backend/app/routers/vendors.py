from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.vendor import Vendor
from app.schemas.vendor import VendorResponse

router = APIRouter(prefix="/api/v1/vendors", tags=["Vendors"])


class VendorCreate(BaseModel):
    name: str
    category: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    vat_number: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    payment_terms: int = 30


@router.post("", response_model=VendorResponse, status_code=201)
async def create_vendor(payload: VendorCreate, db: AsyncSession = Depends(get_db)):
    vendor = Vendor(name=payload.name, category=payload.category,
                    contact_person=payload.contact_person, email=payload.email,
                    phone=payload.phone, vat_number=payload.vat_number,
                    bank_account=payload.bank_account, bank_name=payload.bank_name,
                    payment_terms=payload.payment_terms)
    db.add(vendor)
    await db.flush()
    await db.refresh(vendor)
    return vendor


@router.get("", response_model=list[VendorResponse])
async def list_vendors(
    category: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(Vendor).order_by(Vendor.name)
    if category:
        q = q.where(Vendor.category == category)
    if status:
        q = q.where(Vendor.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    return vendor
