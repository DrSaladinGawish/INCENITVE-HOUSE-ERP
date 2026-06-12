"""Financial reports — all flagged with data-quality metadata."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.journal_voucher import JournalVoucher
from app.models.sales_invoice import SalesInvoice

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])

META_PARTIAL = {
    "basis": "invoice_accrual",
    "coverage_pct": 15.3,
    "cash_basis_available": False,
    "missing_reason": "Source CSV export stripped all monetary values",
    "confidence": "low",
}

META_JV_COMPLETE = {
    "basis": "journal_voucher",
    "coverage_pct": 100.0,
    "cash_basis_available": False,
    "missing_reason": None,
    "confidence": "high",
}


@router.get("/trial-balance")
async def trial_balance(db: AsyncSession = Depends(get_db)):
    """Trial balance from journal vouchers (36 rows, $857K control total)."""
    result = await db.execute(
        select(
            JournalVoucher.debit_account,
            func.sum(JournalVoucher.amount),
            func.count(JournalVoucher.id),
        )
        .group_by(JournalVoucher.debit_account)
        .order_by(JournalVoucher.debit_account)
    )
    debit_balances = [{"account": r[0], "total": float(r[1]), "entries": r[2]} for r in result.all()]

    result = await db.execute(
        select(
            JournalVoucher.credit_account,
            func.sum(JournalVoucher.amount),
            func.count(JournalVoucher.id),
        )
        .group_by(JournalVoucher.credit_account)
        .order_by(JournalVoucher.credit_account)
    )
    credit_balances = [{"account": r[0], "total": float(r[1]), "entries": r[2]} for r in result.all()]

    total_debit = sum(b["total"] for b in debit_balances)
    total_credit = sum(c["total"] for c in credit_balances)
    balanced = abs(total_debit - total_credit) < 0.01

    return {
        "data": {
            "total_entries": sum(b["entries"] for b in debit_balances),
            "total_debit": round(total_debit, 2),
            "total_credit": round(total_credit, 2),
            "balanced": balanced,
            "debit_balances": debit_balances,
            "credit_balances": credit_balances,
        },
        "meta": META_JV_COMPLETE,
    }


@router.get("/revenue-pipeline")
async def revenue_pipeline(db: AsyncSession = Depends(get_db)):
    """Revenue pipeline from sales invoices with amounts (9 SI, $2.2M)."""
    from sqlalchemy import text
    month_trunc = func.date_trunc(text("'month'"), SalesInvoice.invoice_date)
    result = await db.execute(
        select(
            month_trunc.label("month"),
            func.sum(SalesInvoice.total_amount),
            func.count(SalesInvoice.id),
        )
        .where(SalesInvoice.total_amount > 0)
        .group_by(month_trunc)
        .order_by(month_trunc)
    )
    by_month = [{"month": str(r[0]), "total": float(r[1]), "invoices": r[2]} for r in result.all()]

    total_pipeline = sum(m["total"] for m in by_month)

    return {
        "data": {
            "total_pipeline": round(total_pipeline, 2),
            "invoice_count": sum(m["invoices"] for m in by_month),
            "by_month": by_month,
            "basis": "invoice_accrual",
            "bank_confirmed": False,
        },
        "meta": {**META_PARTIAL, "note": "Only 9/59 SI have amounts ($2.2M). Remaining 50 SI lack source data."},
    }
