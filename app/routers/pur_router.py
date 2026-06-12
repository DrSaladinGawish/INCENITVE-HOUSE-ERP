from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import pur_service
from app.schemas.pur import (
    VendorCreate, VendorUpdate, VendorResponse,
    PurchaseVoucherCreate, PurchaseVoucherUpdate, PurchaseVoucherResponse, PurchaseVoucherList,
)

router = APIRouter(prefix="/api/pur", tags=["Purchases"])


@router.get("/vendors", response_model=list[VendorResponse])
def list_vendors(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return pur_service.get_vendors(db, skip=skip, limit=limit)


@router.get("/vendors/{vendor_code}", response_model=VendorResponse)
def get_vendor(vendor_code: str, db: Session = Depends(get_db)):
    vendor = pur_service.get_vendor(db, vendor_code)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return vendor


@router.post("/vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(data: VendorCreate, db: Session = Depends(get_db)):
    return pur_service.create_vendor(db, data)


@router.put("/vendors/{vendor_code}", response_model=VendorResponse)
def update_vendor(vendor_code: str, data: VendorUpdate, db: Session = Depends(get_db)):
    vendor = pur_service.update_vendor(db, vendor_code, data)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return vendor


@router.delete("/vendors/{vendor_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(vendor_code: str, db: Session = Depends(get_db)):
    if not pur_service.delete_vendor(db, vendor_code):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")


@router.get("/vouchers", response_model=PurchaseVoucherList)
def list_vouchers(
    vendor_code: str | None = Query(None),
    pnr_number: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = pur_service.get_purchase_vouchers(db, vendor_code=vendor_code, pnr_number=pnr_number, skip=skip, limit=page_size)
    return PurchaseVoucherList(items=items, total=total, page=page, page_size=page_size)


@router.get("/vouchers/{voucher_id}", response_model=PurchaseVoucherResponse)
def get_voucher(voucher_id: int, db: Session = Depends(get_db)):
    voucher = pur_service.get_purchase_voucher(db, voucher_id)
    if not voucher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voucher not found")
    return voucher


@router.post("/vouchers", response_model=PurchaseVoucherResponse, status_code=status.HTTP_201_CREATED)
def create_voucher(data: PurchaseVoucherCreate, db: Session = Depends(get_db)):
    return pur_service.create_purchase_voucher(db, data)


@router.put("/vouchers/{voucher_id}", response_model=PurchaseVoucherResponse)
def update_voucher(voucher_id: int, data: PurchaseVoucherUpdate, db: Session = Depends(get_db)):
    voucher = pur_service.update_purchase_voucher(db, voucher_id, data)
    if not voucher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voucher not found")
    return voucher


@router.delete("/vouchers/{voucher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_voucher(voucher_id: int, db: Session = Depends(get_db)):
    if not pur_service.delete_purchase_voucher(db, voucher_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voucher not found")
