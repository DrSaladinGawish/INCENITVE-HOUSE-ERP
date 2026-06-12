from uuid import UUID
from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.payment_voucher import PaymentVoucher
from app.schemas.payment_voucher import PaymentVoucherCreate, PaymentVoucherResponse
from app.services.audit_logger import AuditLogger

router = APIRouter(prefix="/api/v1/payment-vouchers", tags=["Payment Vouchers"])


class VoucherStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


_PENDING_STATUSES = ("draft", "pending", "submitted")


def _client_info(request: Request):
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.post("", response_model=PaymentVoucherResponse, status_code=201)
async def create_payment_voucher(payload: PaymentVoucherCreate, request: Request, db: AsyncSession = Depends(get_db)):
    pv = PaymentVoucher(**payload.model_dump())
    db.add(pv)
    await db.flush()
    await db.refresh(pv)
    audit = AuditLogger(db)
    await audit.log(
        action="create",
        target_type="payment_voucher",
        target_id=str(pv.id),
        new_value=payload.model_dump(),
        description=f"Created payment voucher {pv.voucher_number}",
        **_client_info(request),
    )
    return pv


@router.get("", response_model=list[PaymentVoucherResponse])
async def list_payment_vouchers(
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(PaymentVoucher).order_by(PaymentVoucher.payment_date.desc())
    if status:
        q = q.where(PaymentVoucher.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{voucher_id}", response_model=PaymentVoucherResponse)
async def get_payment_voucher(voucher_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaymentVoucher).where(PaymentVoucher.id == voucher_id))
    pv = result.scalar_one_or_none()
    if not pv:
        raise HTTPException(404, "Payment voucher not found")
    return pv


@router.patch("/{voucher_id}/approve")
async def approve_payment_voucher(
    voucher_id: UUID,
    approved_by: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PaymentVoucher).where(PaymentVoucher.id == voucher_id))
    pv = result.scalar_one_or_none()
    if not pv:
        raise HTTPException(404, "Payment voucher not found")
    before = {"status": pv.status}
    pv.status = VoucherStatus.APPROVED
    pv.approved_by = approved_by
    pv.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.flush()
    audit = AuditLogger(db)
    await audit.log(
        action="approve",
        target_type="payment_voucher",
        target_id=str(voucher_id),
        old_value=before,
        new_value={"status": VoucherStatus.APPROVED},
        description=f"Approved payment voucher {pv.voucher_number}",
        actor_id=str(approved_by),
        **_client_info(request),
    )
    return {"status": "approved", "id": str(voucher_id)}


@router.patch("/{voucher_id}/submit")
async def submit_voucher(voucher_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaymentVoucher).where(PaymentVoucher.id == voucher_id))
    pv = result.scalar_one_or_none()
    if not pv:
        raise HTTPException(404, "Voucher not found")
    if pv.status not in ("draft", "pending"):
        raise HTTPException(400, f"Cannot submit from status: {pv.status}")
    before = {"status": pv.status}
    pv.status = VoucherStatus.SUBMITTED
    await db.flush()
    audit = AuditLogger(db)
    await audit.log(
        action="submit",
        target_type="payment_voucher",
        target_id=str(voucher_id),
        old_value=before,
        new_value={"status": VoucherStatus.SUBMITTED},
        description=f"Submitted payment voucher {pv.voucher_number}",
        **_client_info(request),
    )
    return {"status": VoucherStatus.SUBMITTED, "id": str(voucher_id)}


@router.patch("/{voucher_id}/pay")
async def pay_voucher(voucher_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaymentVoucher).where(PaymentVoucher.id == voucher_id))
    pv = result.scalar_one_or_none()
    if not pv:
        raise HTTPException(404, "Voucher not found")
    if pv.status != VoucherStatus.APPROVED:
        raise HTTPException(400, f"Cannot pay from status: {pv.status}")
    before = {"status": pv.status}
    pv.status = VoucherStatus.PAID
    await db.flush()
    audit = AuditLogger(db)
    await audit.log(
        action="pay",
        target_type="payment_voucher",
        target_id=str(voucher_id),
        old_value=before,
        new_value={"status": VoucherStatus.PAID},
        description=f"Paid payment voucher {pv.voucher_number}",
        **_client_info(request),
    )
    return {"status": VoucherStatus.PAID, "id": str(voucher_id)}


@router.patch("/{voucher_id}/cancel")
async def cancel_voucher(voucher_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaymentVoucher).where(PaymentVoucher.id == voucher_id))
    pv = result.scalar_one_or_none()
    if not pv:
        raise HTTPException(404, "Voucher not found")
    if pv.status == VoucherStatus.PAID:
        raise HTTPException(400, "Cannot cancel a paid voucher")
    before = {"status": pv.status}
    pv.status = VoucherStatus.CANCELLED
    await db.flush()
    audit = AuditLogger(db)
    await audit.log(
        action="cancel",
        target_type="payment_voucher",
        target_id=str(voucher_id),
        old_value=before,
        new_value={"status": VoucherStatus.CANCELLED},
        description=f"Cancelled payment voucher {pv.voucher_number}",
        **_client_info(request),
    )
    return {"status": VoucherStatus.CANCELLED, "id": str(voucher_id)}


@router.get("/pending/count")
async def pending_count(
    db: AsyncSession = Depends(get_db),
):
    count = await db.scalar(
        select(func.count(PaymentVoucher.id)).where(PaymentVoucher.status.in_(_PENDING_STATUSES))
    ) or 0
    return Response(content=str(count), media_type="text/plain")
