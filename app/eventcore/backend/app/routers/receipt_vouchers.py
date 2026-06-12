from uuid import UUID
from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.receipt_voucher import ReceiptVoucher
from app.schemas.receipt_voucher import ReceiptVoucherCreate, ReceiptVoucherResponse
from app.services.audit_logger import AuditLogger

router = APIRouter(prefix="/api/v1/receipt-vouchers", tags=["Receipt Vouchers"])


class ReceiptStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    RECEIVED = "received"
    CANCELLED = "cancelled"


_PENDING_STATUSES = ("draft", "pending", "submitted")


def _client_info(request: Request):
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.post("", response_model=ReceiptVoucherResponse, status_code=201)
async def create_receipt_voucher(payload: ReceiptVoucherCreate, request: Request, db: AsyncSession = Depends(get_db)):
    rv = ReceiptVoucher(**payload.model_dump())
    db.add(rv)
    await db.flush()
    await db.refresh(rv)
    audit = AuditLogger(db)
    await audit.log(
        action="create",
        target_type="receipt_voucher",
        target_id=str(rv.id),
        new_value=payload.model_dump(),
        description=f"Created receipt voucher {rv.voucher_number}",
        **_client_info(request),
    )
    return rv


@router.get("", response_model=list[ReceiptVoucherResponse])
async def list_receipt_vouchers(
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(ReceiptVoucher).order_by(ReceiptVoucher.receipt_date.desc())
    if status:
        q = q.where(ReceiptVoucher.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{voucher_id}", response_model=ReceiptVoucherResponse)
async def get_receipt_voucher(voucher_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReceiptVoucher).where(ReceiptVoucher.id == voucher_id))
    rv = result.scalar_one_or_none()
    if not rv:
        raise HTTPException(404, "Receipt voucher not found")
    return rv


@router.patch("/{voucher_id}/receive")
async def receive_receipt_voucher(
    voucher_id: UUID,
    received_by: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ReceiptVoucher).where(ReceiptVoucher.id == voucher_id))
    rv = result.scalar_one_or_none()
    if not rv:
        raise HTTPException(404, "Receipt voucher not found")
    before = {"status": rv.status}
    rv.status = ReceiptStatus.RECEIVED
    rv.received_by = received_by
    rv.received_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.flush()
    audit = AuditLogger(db)
    await audit.log(
        action="receive",
        target_type="receipt_voucher",
        target_id=str(voucher_id),
        old_value=before,
        new_value={"status": ReceiptStatus.RECEIVED},
        description=f"Received receipt voucher {rv.voucher_number}",
        actor_id=str(received_by),
        **_client_info(request),
    )
    return {"status": "received", "id": str(voucher_id)}


@router.patch("/{voucher_id}/submit")
async def submit_receipt(voucher_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReceiptVoucher).where(ReceiptVoucher.id == voucher_id))
    rv = result.scalar_one_or_none()
    if not rv:
        raise HTTPException(404, "Receipt not found")
    if rv.status not in ("draft", "pending"):
        raise HTTPException(400, f"Cannot submit from status: {rv.status}")
    before = {"status": rv.status}
    rv.status = ReceiptStatus.SUBMITTED
    await db.flush()
    audit = AuditLogger(db)
    await audit.log(
        action="submit",
        target_type="receipt_voucher",
        target_id=str(voucher_id),
        old_value=before,
        new_value={"status": ReceiptStatus.SUBMITTED},
        description=f"Submitted receipt voucher {rv.voucher_number}",
        **_client_info(request),
    )
    return {"status": ReceiptStatus.SUBMITTED, "id": str(voucher_id)}


@router.patch("/{voucher_id}/cancel")
async def cancel_receipt(voucher_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReceiptVoucher).where(ReceiptVoucher.id == voucher_id))
    rv = result.scalar_one_or_none()
    if not rv:
        raise HTTPException(404, "Receipt not found")
    if rv.status == ReceiptStatus.RECEIVED:
        raise HTTPException(400, "Cannot cancel a received receipt")
    before = {"status": rv.status}
    rv.status = ReceiptStatus.CANCELLED
    await db.flush()
    audit = AuditLogger(db)
    await audit.log(
        action="cancel",
        target_type="receipt_voucher",
        target_id=str(voucher_id),
        old_value=before,
        new_value={"status": ReceiptStatus.CANCELLED},
        description=f"Cancelled receipt voucher {rv.voucher_number}",
        **_client_info(request),
    )
    return {"status": ReceiptStatus.CANCELLED, "id": str(voucher_id)}


@router.get("/pending/count")
async def pending_count(
    db: AsyncSession = Depends(get_db),
):
    count = await db.scalar(
        select(func.count(ReceiptVoucher.id)).where(ReceiptVoucher.status.in_(_PENDING_STATUSES))
    ) or 0
    return Response(content=str(count), media_type="text/plain")
