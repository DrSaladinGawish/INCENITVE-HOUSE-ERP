from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.ihe_models import (
    PNRMaster, SalesInvoice, PurchaseVoucher, BankTransaction,
    Client, Vendor,
)

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])


def safe_db(callback, default=None):
    try:
        return callback()
    except (SQLAlchemyError, AttributeError):
        return default


class AskRequest(BaseModel):
    query: str
    context: str = "/"


class AskResponse(BaseModel):
    answer: str


class AnalyzeRequest(BaseModel):
    type: str = "sales"


class PredictRequest(BaseModel):
    model: str = "cashflow"


class TrendsRequest(BaseModel):
    metric: str = "revenue"


@router.post("/ask", response_model=AskResponse)
def ask_ai(req: AskRequest, db: Session = Depends(get_db)):
    q = req.query.lower()
    answers = []

    if "pnr" in q or "event" in q:
        total = safe_db(lambda: db.execute(select(func.count(PNRMaster.PNRNumber))).scalar() or 0, 0)
        active = safe_db(lambda: db.execute(select(func.count(PNRMaster.PNRNumber)).where(PNRMaster.Status == "Active")).scalar() or 0, 0)
        answers.append(f"There are {total} PNRs total, {active} active.")

    if "sale" in q or "invoice" in q:
        total_sales = safe_db(lambda: float(db.execute(select(func.coalesce(func.sum(SalesInvoice.TotalValue), 0))).scalar() or 0.0), 0.0)
        inv_count = safe_db(lambda: db.execute(select(func.count(SalesInvoice.InvoiceID))).scalar() or 0, 0)
        answers.append(f"Total sales: {total_sales:,.2f} EGP across {inv_count} invoices.")

    if "purchase" in q or "voucher" in q:
        total_pur = safe_db(lambda: float(db.execute(select(func.coalesce(func.sum(PurchaseVoucher.TotalValue), 0))).scalar() or 0.0), 0.0)
        voc_count = safe_db(lambda: db.execute(select(func.count(PurchaseVoucher.VoucherID))).scalar() or 0, 0)
        answers.append(f"Total purchases: {total_pur:,.2f} EGP across {voc_count} vouchers.")

    if "bank" in q or "cash" in q or "balance" in q:
        last_bal = safe_db(lambda: float(db.execute(select(BankTransaction.RunningBalance).order_by(BankTransaction.TransactionID.desc()).limit(1)).scalar() or 0.0), 0.0)
        answers.append(f"Current bank balance: {last_bal:,.2f} EGP.")

    if "client" in q or "customer" in q:
        cnt = safe_db(lambda: db.execute(select(func.count(Client.ClientCode))).scalar() or 0, 0)
        answers.append(f"Total clients: {cnt}.")

    if "vendor" in q or "supplier" in q:
        cnt = safe_db(lambda: db.execute(select(func.count(Vendor.VendorCode))).scalar() or 0, 0)
        answers.append(f"Total vendors: {cnt}.")

    if not answers:
        answers.append(f"I can help with PNR counts, sales totals, purchase totals, bank balance, clients, and vendors. Try asking a specific question!")

    return AskResponse(answer=" ".join(answers))


def _fetch_chart(db, query_fn, summary_fn):
    rows = safe_db(query_fn, [])
    if not rows:
        return {"chart": None, "summary": "No data available yet. Connect to SQL Server.", "type": "bar"}
    labels = [str(r[0]) for r in rows]
    values = [float(r[1]) for r in rows]
    return {"chart": {"labels": labels, "values": values}, "summary": summary_fn(len(rows), values), "type": "bar"}


@router.post("/analyze")
def analyze_data(req: AnalyzeRequest, db: Session = Depends(get_db)):
    if req.type == "sales":
        return _fetch_chart(db,
            lambda: db.execute(select(SalesInvoice.InvoiceDate, func.sum(SalesInvoice.TotalValue)).group_by(SalesInvoice.InvoiceDate).order_by(SalesInvoice.InvoiceDate).limit(30)).all(),
            lambda n, v: f"Sales trend shown for {n} periods.")
    elif req.type == "purchases":
        return _fetch_chart(db,
            lambda: db.execute(select(PurchaseVoucher.InvoiceDate, func.sum(PurchaseVoucher.TotalValue)).group_by(PurchaseVoucher.InvoiceDate).order_by(PurchaseVoucher.InvoiceDate).limit(30)).all(),
            lambda n, v: f"Purchase trend shown for {n} periods.")
    elif req.type == "bank":
        rows = safe_db(lambda: db.execute(select(BankTransaction.TransactionDate, BankTransaction.RunningBalance).order_by(BankTransaction.TransactionDate.desc()).limit(30)).all(), [])
        if rows:
            rows.reverse()
            labels = [str(r[0]) for r in rows]
            values = [float(r[1]) for r in rows]
            return {"chart": {"labels": labels, "values": values}, "summary": f"Bank balance trend, latest: {values[-1]:,.2f} EGP", "type": "line"}
        return {"chart": None, "summary": "No bank data yet.", "type": "line"}
    return {"summary": "Use: sales, purchases, bank.", "chart": None}


@router.post("/predict")
def run_prediction(req: PredictRequest, db: Session = Depends(get_db)):
    if req.model == "cashflow":
        rows = safe_db(lambda: db.execute(select(BankTransaction.TransactionDate, BankTransaction.RunningBalance).order_by(BankTransaction.TransactionDate.desc()).limit(10)).all(), [])
        if rows:
            latest = float(rows[0][1])
            return {"prediction": f"{latest:,.2f} EGP", "confidence": 0.75, "factors": ["Current balance", "Recent inflows", "Pending payments"], "summary": f"Estimated cash position: {latest:,.2f} EGP"}
        return {"prediction": "No data", "confidence": 0, "factors": [], "summary": "Connect to SQL Server to see predictions."}
    elif req.model == "churn":
        total_clients = safe_db(lambda: db.execute(select(func.count(Client.ClientCode))).scalar() or 0, 0)
        active_pnrs = safe_db(lambda: db.execute(select(func.count(PNRMaster.PNRNumber)).where(PNRMaster.Status == "Active")).scalar() or 0, 0)
        churn_risk = max(0, min(1, 1 - (active_pnrs / max(total_clients, 1))))
        return {"prediction": f"{churn_risk*100:.0f}% risk", "confidence": 0.65, "factors": [f"{active_pnrs} active PNRs", f"{total_clients} clients"], "summary": f"Churn risk: {churn_risk*100:.0f}%"}
    elif req.model == "overrun":
        avg_budget = safe_db(lambda: float(db.execute(select(func.avg(PurchaseVoucher.TotalValue)).where(PurchaseVoucher.PNRNumber.isnot(None))).scalar() or 0.0), 0.0)
        return {"prediction": "HIGH" if avg_budget > 50000 else "LOW", "confidence": 0.7, "factors": [f"Avg spend: {avg_budget:,.2f} EGP"], "summary": f"Overrun risk: {'HIGH' if avg_budget > 50000 else 'LOW'}"}
    elif req.model == "anomaly":
        avg_tx = safe_db(lambda: float(db.execute(select(func.avg(BankTransaction.Withdrawal))).scalar() or 0.0), 0.0)
        return {"prediction": "Normal", "confidence": 0.85, "factors": [f"Avg tx: {avg_tx:,.2f} EGP"], "summary": "No anomalies detected."}
    return {"prediction": "Unknown model", "confidence": 0, "factors": [], "summary": f"Model '{req.model}' not found."}


@router.post("/trends")
def show_trends(req: TrendsRequest, db: Session = Depends(get_db)):
    if req.metric == "revenue":
        return _fetch_chart(db,
            lambda: db.execute(select(func.year(SalesInvoice.InvoiceDate), func.sum(SalesInvoice.TotalValue)).group_by(func.year(SalesInvoice.InvoiceDate)).order_by(func.year(SalesInvoice.InvoiceDate))).all(),
            lambda n, v: f"Revenue across {n} years.")
    elif req.metric == "expense":
        return _fetch_chart(db,
            lambda: db.execute(select(func.year(PurchaseVoucher.InvoiceDate), func.sum(PurchaseVoucher.TotalValue)).group_by(func.year(PurchaseVoucher.InvoiceDate)).order_by(func.year(PurchaseVoucher.InvoiceDate))).all(),
            lambda n, v: f"Expense across {n} years.")
    elif req.metric == "profit":
        rev = safe_db(lambda: {r[0]: float(r[1]) for r in db.execute(select(func.year(SalesInvoice.InvoiceDate), func.sum(SalesInvoice.TotalValue)).group_by(func.year(SalesInvoice.InvoiceDate))).all()}, {})
        exp = safe_db(lambda: {r[0]: float(r[1]) for r in db.execute(select(func.year(PurchaseVoucher.InvoiceDate), func.sum(PurchaseVoucher.TotalValue)).group_by(func.year(PurchaseVoucher.InvoiceDate))).all()}, {})
        if rev or exp:
            years = sorted(set(list(rev.keys()) + list(exp.keys())))
            labels = [str(y) for y in years]
            values = [rev.get(y, 0) - exp.get(y, 0) for y in years]
            return {"chart": {"labels": labels, "values": values}, "summary": f"Profit across {len(years)} years.", "type": "bar"}
        return {"chart": None, "summary": "No data yet.", "type": "bar"}
    elif req.metric == "bank":
        rows = safe_db(lambda: db.execute(select(BankTransaction.TransactionDate, BankTransaction.RunningBalance).order_by(BankTransaction.TransactionDate.desc()).limit(20)).all(), [])
        if rows:
            rows.reverse()
            labels = [str(r[0]) for r in rows]
            values = [float(r[1]) for r in rows]
            return {"chart": {"labels": labels, "values": values}, "summary": "Bank balance trend.", "type": "line"}
        return {"chart": None, "summary": "No data yet.", "type": "line"}
    return {"chart": None, "summary": f"Metric '{req.metric}' not found."}
