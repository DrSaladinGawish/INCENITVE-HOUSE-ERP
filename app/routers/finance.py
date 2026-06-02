import json
import datetime
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.database import get_db
from app.models.models import SalesInvoice, PurchaseInvoice, InvoicePayment, AuditTrail, EventDim
from app.schemas import AuditTrailResponse
from app.routers.auth import get_current_user, require_role

router = APIRouter(tags=["finance"])


@router.get("/invoices/sales")
async def list_finance_sales_invoices(
    status: Optional[str] = None,
    overdue: Optional[bool] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(SalesInvoice)
    if status:
        q = q.where(SalesInvoice.status == status)
    if overdue:
        today = datetime.date.today()
        q = q.where(SalesInvoice.due_date < today).where(SalesInvoice.status.in_(["pending", "overdue"]))
    q = q.offset(offset).limit(limit).order_by(SalesInvoice.inv_id.desc())
    result = await db.execute(q)
    return [{"inv_id": r.inv_id, "invoice_no": r.invoice_no, "client_name": r.client_name, "total_amount": r.total_amount, "paid_amount": r.paid_amount, "balance": r.total_amount - r.paid_amount, "due_date": str(r.due_date) if r.due_date else None, "status": r.status} for r in result.scalars().all()]


@router.get("/invoices/purchases")
async def list_finance_purchase_invoices(
    status: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(PurchaseInvoice)
    if status:
        q = q.where(PurchaseInvoice.status == status)
    q = q.offset(offset).limit(limit).order_by(PurchaseInvoice.inv_id.desc())
    result = await db.execute(q)
    return [{"inv_id": r.inv_id, "invoice_no": r.invoice_no, "vendor_name": r.vendor_name, "total_amount": r.total_amount, "paid_amount": r.paid_amount, "balance": r.total_amount - r.paid_amount, "due_date": str(r.due_date) if r.due_date else None, "status": r.status} for r in result.scalars().all()]


@router.post("/invoices/approve/{inv_id}")
async def approve_invoice(
    inv_id: int,
    invoice_type: str = Query("sales"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "accountant")),
):
    model_cls = SalesInvoice if invoice_type == "sales" else PurchaseInvoice
    result = await db.execute(select(model_cls).where(model_cls.inv_id == inv_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    old_status = inv.status
    inv.status = "approved"
    await db.commit()
    audit = AuditTrail(table_name=model_cls.__tablename__, record_id=inv_id, action="APPROVE", old_values={"status": old_status}, new_values={"status": "approved"}, changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": "Invoice approved", "inv_id": inv_id, "invoice_type": invoice_type}


@router.get("/invoices/overdue")
async def overdue_invoices(db: AsyncSession = Depends(get_db)):
    today = datetime.date.today()
    ninety_days_ago = today - datetime.timedelta(days=90)
    result = await db.execute(
        select(SalesInvoice).where(SalesInvoice.due_date < today).where(SalesInvoice.status.in_(["pending", "overdue"])).order_by(SalesInvoice.due_date)
    )
    return [{"inv_id": r.inv_id, "invoice_no": r.invoice_no, "client_name": r.client_name, "total_amount": r.total_amount, "paid_amount": r.paid_amount, "balance": r.total_amount - r.paid_amount, "due_date": str(r.due_date) if r.due_date else None, "days_overdue": (today - r.due_date).days if r.due_date else 0} for r in result.scalars().all()]


@router.post("/payments/record")
async def record_payment(
    invoice_type: str = Query("sales"),
    invoice_id: int = Query(...),
    amount: float = Query(...),
    payment_method: str = "cash",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "accountant")),
):
    model_cls = SalesInvoice if invoice_type == "sales" else PurchaseInvoice
    result = await db.execute(select(model_cls).where(model_cls.inv_id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    payment = InvoicePayment(invoice_type=invoice_type, invoice_id=invoice_id, payment_date=datetime.date.today(), amount=amount, payment_method=payment_method)
    db.add(payment)
    inv.paid_amount = (inv.paid_amount or 0) + amount
    if inv.paid_amount >= inv.total_amount:
        inv.status = "paid"
    await db.commit()
    audit = AuditTrail(table_name="invoice_payments", action="RECORD_PAYMENT", new_values={"invoice_type": invoice_type, "invoice_id": invoice_id, "amount": amount, "method": payment_method}, changed_by=current_user["username"])
    db.add(audit)
    await db.commit()
    return {"detail": "Payment recorded", "invoice_id": invoice_id, "amount": amount, "new_balance": inv.total_amount - inv.paid_amount}


@router.get("/audit", response_model=list[AuditTrailResponse])
async def get_audit_trail(
    table_name: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(AuditTrail).order_by(AuditTrail.changed_at.desc())
    if table_name:
        q = q.where(AuditTrail.table_name == table_name)
    if action:
        q = q.where(AuditTrail.action == action)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/aging-report")
async def aging_report(db: AsyncSession = Depends(get_db)):
    today = datetime.date.today()
    result = await db.execute(
        select(SalesInvoice).where(SalesInvoice.status.in_(["pending", "overdue"])).order_by(SalesInvoice.due_date)
    )
    invoices = result.scalars().all()
    buckets = {"0-30": [], "31-60": [], "61-90": [], "91+": []}
    for inv in invoices:
        if not inv.due_date:
            buckets["91+"].append(inv)
            continue
        days = (today - inv.due_date).days
        if days <= 0:
            continue
        elif days <= 30:
            buckets["0-30"].append(inv)
        elif days <= 60:
            buckets["31-60"].append(inv)
        elif days <= 90:
            buckets["61-90"].append(inv)
        else:
            buckets["91+"].append(inv)
    return {
        bucket: [{"inv_id": i.inv_id, "invoice_no": i.invoice_no, "client_name": i.client_name, "balance": i.total_amount - i.paid_amount, "due_date": str(i.due_date) if i.due_date else None} for i in items]
        for bucket, items in buckets.items()
    }


@router.get("/cash-flow-projections")
async def cash_flow_projections(days: int = Query(30, le=365), db: AsyncSession = Depends(get_db)):
    today = datetime.date.today()
    horizon = today + datetime.timedelta(days=days)
    result = await db.execute(
        select(SalesInvoice).where(SalesInvoice.status.in_(["pending", "overdue"])).where(SalesInvoice.due_date <= horizon)
    )
    receivables = result.scalars().all()
    result2 = await db.execute(
        select(PurchaseInvoice).where(PurchaseInvoice.status.in_(["pending", "overdue"])).where(PurchaseInvoice.due_date <= horizon)
    )
    payables = result2.scalars().all()
    total_in = sum((r.total_amount - r.paid_amount) for r in receivables)
    total_out = sum((p.total_amount - p.paid_amount) for p in payables)
    return {"projection_days": days, "expected_inflow": total_in, "expected_outflow": total_out, "net_position": total_in - total_out}
