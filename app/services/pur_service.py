from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.ihe_models import Vendor, PurchaseVoucher, PurchaseVoucherLine
from app.schemas.pur import VendorCreate, VendorUpdate, PurchaseVoucherCreate


def get_vendors(db: Session, skip: int = 0, limit: int = 100) -> list[Vendor]:
    stmt = select(Vendor).order_by(Vendor.VendorCode).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_vendor(db: Session, vendor_code: str) -> Vendor | None:
    return db.get(Vendor, vendor_code)


def create_vendor(db: Session, data: VendorCreate) -> Vendor:
    vendor = Vendor(**data.model_dump())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


def update_vendor(db: Session, vendor_code: str, data: VendorUpdate) -> Vendor | None:
    vendor = db.get(Vendor, vendor_code)
    if not vendor:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(vendor, key, val)
    db.commit()
    db.refresh(vendor)
    return vendor


def delete_vendor(db: Session, vendor_code: str) -> bool:
    vendor = db.get(Vendor, vendor_code)
    if not vendor:
        return False
    db.delete(vendor)
    db.commit()
    return True


def get_purchase_vouchers(
    db: Session,
    vendor_code: str | None = None,
    pnr_number: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[PurchaseVoucher], int]:
    stmt = select(PurchaseVoucher).options(joinedload(PurchaseVoucher.lines))
    count_stmt = select(func.count(PurchaseVoucher.VoucherID))
    if vendor_code:
        stmt = stmt.join(PurchaseVoucherLine).where(PurchaseVoucherLine.VendorCode == vendor_code)
        count_stmt = count_stmt.join(PurchaseVoucherLine).where(PurchaseVoucherLine.VendorCode == vendor_code)
    if pnr_number:
        stmt = stmt.where(PurchaseVoucher.PNRNumber == pnr_number)
        count_stmt = count_stmt.where(PurchaseVoucher.PNRNumber == pnr_number)
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.order_by(PurchaseVoucher.InvoiceDate.desc()).offset(skip).limit(limit)
    items = list(db.execute(stmt).scalars().unique().all())
    return items, total


def create_purchase_voucher(db: Session, data: PurchaseVoucherCreate) -> PurchaseVoucher:
    lines_data = data.lines
    voc_data = data.model_dump(exclude={"lines"})
    voucher = PurchaseVoucher(**voc_data)
    db.add(voucher)
    db.flush()
    for line_data in lines_data:
        line = PurchaseVoucherLine(VoucherID=voucher.VoucherID, **line_data.model_dump())
        db.add(line)
    db.commit()
    db.refresh(voucher)
    return voucher


def get_purchase_voucher(db: Session, voucher_id: int) -> PurchaseVoucher | None:
    stmt = select(PurchaseVoucher).where(PurchaseVoucher.VoucherID == voucher_id).options(joinedload(PurchaseVoucher.lines))
    return db.execute(stmt).unique().scalar_one_or_none()


def update_purchase_voucher(db: Session, voucher_id: int, data) -> PurchaseVoucher | None:
    voucher = db.get(PurchaseVoucher, voucher_id)
    if not voucher:
        return None
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(voucher, key, val)
    db.commit()
    db.refresh(voucher)
    return voucher


def delete_purchase_voucher(db: Session, voucher_id: int) -> bool:
    voucher = db.get(PurchaseVoucher, voucher_id)
    if not voucher:
        return False
    db.delete(voucher)
    db.commit()
    return True
