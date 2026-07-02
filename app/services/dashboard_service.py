from datetime import datetime
from sqlalchemy import select, func, extract
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.ihe_models import PNRMaster, SalesInvoice, PurchaseVoucher, BankTransaction, Client, Vendor
from app.schemas.dashboard import DashboardSummary


def _safe_val(callback, default=0):
    try:
        return callback()
    except SQLAlchemyError:
        return default


def get_monthly_data(db: Session) -> list[dict]:
    months = []
    for m in range(1, 13):
        revenue = _safe_val(lambda m=m: float(db.execute(
            select(func.coalesce(func.sum(SalesInvoice.TotalValue), 0))
            .where(extract("month", SalesInvoice.InvoiceDate) == m)
        ).scalar() or 0.0))
        expenses = _safe_val(lambda m=m: float(db.execute(
            select(func.coalesce(func.sum(PurchaseVoucher.TotalValue), 0))
            .where(extract("month", PurchaseVoucher.InvoiceDate) == m)
        ).scalar() or 0.0))
        months.append({
            "month": datetime(2000, m, 1).strftime("%b"),
            "revenue": revenue,
            "expenses": expenses,
            "net": revenue - expenses,
        })
    return months


def get_dashboard_summary(db: Session) -> DashboardSummary:
    total_pnrs = _safe_val(lambda: db.execute(select(func.count(PNRMaster.PNRNumber))).scalar() or 0)
    active_pnrs = _safe_val(lambda: db.execute(select(func.count(PNRMaster.PNRNumber)).where(PNRMaster.Status == "Active")).scalar() or 0)
    total_sales = _safe_val(lambda: float(db.execute(select(func.coalesce(func.sum(SalesInvoice.TotalValue), 0))).scalar() or 0.0))
    total_purchases = _safe_val(lambda: float(db.execute(select(func.coalesce(func.sum(PurchaseVoucher.TotalValue), 0))).scalar() or 0.0))
    last_tx = _safe_val(lambda: float(db.execute(select(BankTransaction.RunningBalance).order_by(BankTransaction.TransactionID.desc()).limit(1)).scalar() or 0.0))
    outstanding = _safe_val(lambda: float(db.execute(select(func.coalesce(func.sum(SalesInvoice.TotalValue - SalesInvoice.CollectedAmount), 0)).where(SalesInvoice.PaymentStatus != "Paid")).scalar() or 0.0))
    total_clients = _safe_val(lambda: db.execute(select(func.count(Client.ClientCode))).scalar() or 0)
    total_vendors = _safe_val(lambda: db.execute(select(func.count(Vendor.VendorCode))).scalar() or 0)

    return DashboardSummary(
        total_pnrs=total_pnrs,
        active_pnrs=active_pnrs,
        total_sales=float(total_sales),
        total_purchases=float(total_purchases),
        bank_balance=float(last_tx),
        outstanding_receivables=float(outstanding),
        total_clients=total_clients,
        total_vendors=total_vendors,
    )
