"""Data quality endpoint — density checks and monetary repair."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.bank_transaction import BankTransaction
from app.models.purchase_invoice import PurchaseInvoice
from app.models.payment_voucher import PaymentVoucher
from app.models.sales_invoice import SalesInvoice
from app.models.journal_voucher import JournalVoucher
from app.models.receipt_voucher import ReceiptVoucher

router = APIRouter(prefix="/api/v1/data-quality", tags=["Data Quality"])


@router.get("/summary")
async def data_quality_summary(db: AsyncSession = Depends(get_db)):
    bt_total = await db.scalar(select(func.count(BankTransaction.id))) or 0
    bt_with_amt = await db.scalar(
        select(func.count(BankTransaction.id)).where(BankTransaction.amount > 0)
    ) or 0

    pi_total = await db.scalar(select(func.count(PurchaseInvoice.id))) or 0
    pi_with_amt = await db.scalar(
        select(func.count(PurchaseInvoice.id)).where(PurchaseInvoice.total_amount > 0)
    ) or 0

    pv_total = await db.scalar(select(func.count(PaymentVoucher.id))) or 0
    pv_with_amt = await db.scalar(
        select(func.count(PaymentVoucher.id)).where(PaymentVoucher.amount > 0)
    ) or 0

    si_total = await db.scalar(select(func.count(SalesInvoice.id))) or 0
    si_with_amt = await db.scalar(
        select(func.count(SalesInvoice.id)).where(SalesInvoice.total_amount > 0)
    ) or 0
    si_total_value = float(
        await db.scalar(
            select(func.coalesce(func.sum(SalesInvoice.total_amount), 0))
            .where(SalesInvoice.total_amount > 0)
        ) or 0
    )

    jv_total = await db.scalar(select(func.count(JournalVoucher.id))) or 0
    jv_with_amt = await db.scalar(
        select(func.count(JournalVoucher.id)).where(JournalVoucher.amount > 0)
    ) or 0
    jv_total_value = float(
        await db.scalar(
            select(func.coalesce(func.sum(JournalVoucher.amount), 0))
            .where(JournalVoucher.amount > 0)
        ) or 0
    )

    rv_total = await db.scalar(select(func.count(ReceiptVoucher.id))) or 0
    rv_with_amt = await db.scalar(
        select(func.count(ReceiptVoucher.id)).where(ReceiptVoucher.amount > 0)
    ) or 0

    total_rows = bt_total + pi_total + pv_total + si_total + jv_total + rv_total
    total_with_amt = bt_with_amt + pi_with_amt + pv_with_amt + si_with_amt + jv_with_amt + rv_with_amt

    return {
        "bank_transactions": {"total": bt_total, "with_amount": bt_with_amt, "pct": round(bt_with_amt / bt_total * 100, 1) if bt_total else 0},
        "purchase_invoices": {"total": pi_total, "with_amount": pi_with_amt, "pct": round(pi_with_amt / pi_total * 100, 1) if pi_total else 0},
        "payment_vouchers": {"total": pv_total, "with_amount": pv_with_amt, "pct": round(pv_with_amt / pv_total * 100, 1) if pv_total else 0},
        "sales_invoices": {"total": si_total, "with_amount": si_with_amt, "pct": round(si_with_amt / si_total * 100, 1) if si_total else 0, "total_value": round(si_total_value, 2)},
        "journal_vouchers": {"total": jv_total, "with_amount": jv_with_amt, "pct": round(jv_with_amt / jv_total * 100, 1) if jv_total else 0, "total_value": round(jv_total_value, 2)},
        "receipt_vouchers": {"total": rv_total, "with_amount": rv_with_amt, "pct": round(rv_with_amt / rv_total * 100, 1) if rv_total else 0},
        "total_rows_across_tables": total_rows,
        "total_rows_with_amounts": total_with_amt,
        "overall_data_density_pct": round(total_with_amt / total_rows * 100, 1) if total_rows else 0,
        "reporting_basis": "invoice_accrual_partial",
        "cash_basis_available": False,
        "warning": "Source CSV export stripped all monetary values. Only {0} of {1} rows ({2}%) carry financial amounts.".format(
            total_with_amt, total_rows,
            round(total_with_amt / total_rows * 100, 1) if total_rows else 0
        ),
    }


@router.get("/overview")
async def data_quality_overview(db: AsyncSession = Depends(get_db)):
    """Human-readable overview of system data completeness."""
    summary = await data_quality_summary(db)
    lines = [
        "=" * 60,
        "DATA QUALITY REPORT",
        "=" * 60,
        "",
        f"Overall density: {summary['overall_data_density_pct']}% ({summary['total_rows_with_amounts']}/{summary['total_rows_across_tables']} rows)",
        f"Basis: {summary['reporting_basis']}",
        f"Cash available: {summary['cash_basis_available']}",
        f"Warning: {summary['warning']}",
        "",
        "Table breakdown:",
    ]
    for name, info in [
        ("Bank transactions", "bank_transactions"),
        ("Purchase invoices", "purchase_invoices"),
        ("Payment vouchers", "payment_vouchers"),
        ("Sales invoices", "sales_invoices"),
        ("Journal vouchers", "journal_vouchers"),
        ("Receipt vouchers", "receipt_vouchers"),
    ]:
        d = summary[info]
        value = f", value=${d['total_value']:,.2f}" if d.get("total_value") else ""
        lines.append(f"  {name:25} {d['with_amount']:>4}/{d['total']} ({d['pct']:>5.1f}%){value}")

    return {"report": "\n".join(lines), "data": summary}


@router.get("/density")
async def get_density(db: AsyncSession = Depends(get_db)):
    """Returns % of financial rows carrying non-null monetary values."""
    summary = await data_quality_summary(db)
    tables_data = {k: v for k, v in summary.items() if isinstance(v, dict) and "total" in v}
    return {
        "total_rows": summary["total_rows_across_tables"],
        "rows_with_amount": summary["total_rows_with_amounts"],
        "density_percent": summary["overall_data_density_pct"],
        "tables_checked": list(tables_data.keys()),
        "missing_by_table": {k: v["total"] - v["with_amount"] for k, v in tables_data.items()},
    }


@router.post("/repair")
async def repair_amounts(db: AsyncSession = Depends(get_db)):
    """Backfills missing monetary values from child line_items into parent records."""
    repaired = 0
    tables_affected = []
    warnings = []

    # 1. Repair sales_invoices from sales_invoice_line_items
    try:
        result = await db.execute(text("""
            UPDATE sales_invoices
            SET total_amount = (
                SELECT COALESCE(SUM(COALESCE(total_amount, 0)), 0)
                FROM sales_invoice_line_items
                WHERE sales_invoice_line_items.invoice_id = sales_invoices.id
            )
            WHERE total_amount IS NULL OR total_amount = 0
        """))
        await db.execute(text("""
            UPDATE sales_invoices
            SET subtotal = total_amount * 100.0 / 114.0
            WHERE total_amount > 0 AND (subtotal IS NULL OR subtotal = 0)
        """))
        await db.execute(text("""
            UPDATE sales_invoices
            SET vat_amount = total_amount - subtotal
            WHERE total_amount > 0 AND (vat_amount IS NULL OR vat_amount = 0)
        """))
        rowcount = result.rowcount
        if rowcount > 0:
            repaired += rowcount
            tables_affected.append("sales_invoices")
    except Exception as e:
        warnings.append(f"sales_invoices repair: {str(e)}")

    # 2. Repair purchase_invoices from job_line_items (cost rows)
    try:
        result = await db.execute(text("""
            UPDATE purchase_invoices
            SET total_amount = (
                SELECT COALESCE(SUM(COALESCE(j.total_amount, 0)), 0)
                FROM job_line_items j
                WHERE j.source_type = 'purchase_invoice'
                  AND CAST(j.source_id AS TEXT) = CAST(purchase_invoices.id AS TEXT)
            )
            WHERE total_amount IS NULL OR total_amount = 0
        """))
        rowcount = result.rowcount
        if rowcount > 0:
            repaired += rowcount
            tables_affected.append("purchase_invoices")
    except Exception as e:
        warnings.append(f"purchase_invoices repair: {str(e)}")

    # 3. Repair payment_vouchers from purchase_invoices (via job_id)
    try:
        result = await db.execute(text("""
            UPDATE payment_vouchers
            SET amount = (
                SELECT COALESCE(SUM(COALESCE(pi.total_amount, 0)), 0)
                FROM purchase_invoices pi
                WHERE pi.job_id = payment_vouchers.job_id
            )
            WHERE amount IS NULL OR amount = 0
        """))
        rowcount = result.rowcount
        if rowcount > 0:
            repaired += rowcount
            tables_affected.append("payment_vouchers")
    except Exception as e:
        warnings.append(f"payment_vouchers repair: {str(e)}")

    # 4. Repair receipt_vouchers from sales_invoices (via job_id)
    try:
        result = await db.execute(text("""
            UPDATE receipt_vouchers
            SET amount = (
                SELECT COALESCE(SUM(COALESCE(si.total_amount, 0)), 0)
                FROM sales_invoices si
                WHERE si.job_id = receipt_vouchers.job_id
            )
            WHERE amount IS NULL OR amount = 0
        """))
        rowcount = result.rowcount
        if rowcount > 0:
            repaired += rowcount
            tables_affected.append("receipt_vouchers")
    except Exception as e:
        warnings.append(f"receipt_vouchers repair: {str(e)}")

    await db.commit()

    return {
        "repaired_records": repaired,
        "tables_affected": tables_affected,
        "backfilled_from": "sales_invoice_line_items, job_line_items, purchase_invoices, sales_invoices",
        "warnings": warnings,
    }
