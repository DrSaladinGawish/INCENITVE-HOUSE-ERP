"""
neural_live.py — P4: Wire ML predictors to live SQL Server data.
Falls back to mock predictions when SQL Server is offline.
"""

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_safe import check_sql_available, MOCK_DASHBOARD
from app.services.neural import (
    CashFlowPredictor,
    ClientChurnPredictor,
    PnrOverrunPredictor,
    TransactionAnomalyDetector,
    FeatureEngineer,
    ModelRegistry,
)

router = APIRouter(prefix="/api/v1/neural", tags=["Neural Live"])


class CashflowRequest(BaseModel):
    months: int = 3
    account_code: str = "BNK_CUR"


class CashflowResponse(BaseModel):
    predictions: list[float]
    confidence: float
    source: str


class ChurnRequest(BaseModel):
    client_code: str


class ChurnResponse(BaseModel):
    churn_probability: float
    risk_level: str
    factors: list[str]
    source: str


class OverrunRequest(BaseModel):
    pnr_number: str


class OverrunResponse(BaseModel):
    predicted_final: float
    overrun_percentage: float
    risk_level: str
    source: str


class AnomalyRequest(BaseModel):
    table: str = "BankTransaction"
    days: int = 30


class AnomalyResponse(BaseModel):
    anomaly_count: int
    anomalies: list[dict[str, Any]]
    severity: str
    source: str


MOCK_CASHFLOW = CashflowResponse(
    predictions=[12.5, 14.2, 11.8, 15.3, 13.1, 16.2],
    confidence=0.85,
    source="mock"
)

MOCK_CHURN = ChurnResponse(
    churn_probability=0.12,
    risk_level="low",
    factors=["high engagement", "frequent invoices", "long relationship"],
    source="mock"
)

MOCK_OVERRUN = OverrunResponse(
    predicted_final=1250000.0,
    overrun_percentage=4.2,
    risk_level="low",
    source="mock"
)

MOCK_ANOMALY = AnomalyResponse(
    anomaly_count=2,
    anomalies=[
        {"transaction_id": 1045, "amount": 850000, "reason": "Amount 3.2x above avg", "risk": "medium"},
        {"transaction_id": 2091, "amount": 620000, "reason": "Unusual vendor pattern", "risk": "low"},
    ],
    severity="medium",
    source="mock"
)


@router.post("/cashflow-predict", response_model=CashflowResponse)
def predict_cashflow(req: CashflowRequest, db: Session = Depends(get_db)):
    if db is None:
        return MOCK_CASHFLOW
    try:
        from app.models.ihe_models import BankTransaction
        stmt = (
            select(
                func.date_trunc("month", BankTransaction.TransactionDate).label("month"),
                func.sum(BankTransaction.Deposit - BankTransaction.Withdrawal).label("net"),
            )
            .where(BankTransaction.BankCode == req.account_code)
            .where(BankTransaction.TransactionDate >= func.dateadd(func.month, -12, func.current_date()))
            .group_by(func.date_trunc("month", BankTransaction.TransactionDate))
            .order_by("month")
        )
        rows = db.execute(stmt).all()
        historical = [float(r.net) for r in rows if r.net]
        if not historical:
            return MOCK_CASHFLOW
        predictor = CashFlowPredictor()
        predictions = predictor.predict(historical, steps=req.months)
        confidence = 0.92 if len(historical) >= 6 else 0.75
        return CashflowResponse(predictions=predictions, confidence=confidence, source="live")
    except Exception as e:
        return CashflowResponse(predictions=MOCK_CASHFLOW.predictions[:req.months], confidence=0.5, source=f"fallback: {e}")


@router.post("/client-churn", response_model=ChurnResponse)
def predict_churn(req: ChurnRequest, db: Session = Depends(get_db)):
    if db is None:
        return MOCK_CHURN
    try:
        from app.models.ihe_models import Client, SalesInvoice
        stmt = (
            select(
                Client.ClientCode,
                func.count(SalesInvoice.InvoiceID).label("invoice_count"),
                func.coalesce(func.sum(SalesInvoice.TotalValue), 0).label("total_revenue"),
                func.coalesce(func.max(SalesInvoice.InvoiceDate), "1900-01-01").label("last_invoice"),
            )
            .outerjoin(SalesInvoice, Client.ClientCode == SalesInvoice.ClientCode)
            .where(Client.ClientCode == req.client_code)
            .group_by(Client.ClientCode)
        )
        row = db.execute(stmt).first()
        if not row:
            raise HTTPException(status_code=404, detail="Client not found")
        predictor = ClientChurnPredictor()
        result = predictor.predict({
            "invoice_count": row.invoice_count,
            "total_revenue": float(row.total_revenue),
            "days_since_last": (datetime.now(timezone.utc).date() - row.last_invoice).days if row.last_invoice else 365,
        })
        return ChurnResponse(**result, source="live")
    except HTTPException:
        raise
    except Exception as e:
        return ChurnResponse(churn_probability=0.5, risk_level="unknown", factors=[str(e)], source=f"fallback")


@router.post("/pnr-overrun", response_model=OverrunResponse)
def predict_overrun(req: OverrunRequest, db: Session = Depends(get_db)):
    if db is None:
        return MOCK_OVERRUN
    try:
        from app.models.ihe_models import PNRMaster, PNRBudgetLineItem, PurchaseVoucher
        pnr = db.get(PNRMaster, req.pnr_number)
        if not pnr:
            raise HTTPException(status_code=404, detail="PNR not found")
        budget = db.execute(
            select(func.coalesce(func.sum(PNRBudgetLineItem.Amount), 0))
            .where(PNRBudgetLineItem.JobFolder == req.pnr_number)
        ).scalar() or 0
        actual = db.execute(
            select(func.coalesce(func.sum(PurchaseVoucher.TotalValue), 0))
            .where(PurchaseVoucher.PNRNumber == req.pnr_number)
        ).scalar() or 0
        predictor = PnrOverrunPredictor()
        result = predictor.predict({"budget": float(budget), "actual": float(actual)})
        return OverrunResponse(**result, source="live")
    except HTTPException:
        raise
    except Exception as e:
        return OverrunResponse(predicted_final=0, overrun_percentage=0, risk_level="unknown", source=f"fallback: {e}")


@router.post("/anomaly-detect", response_model=AnomalyResponse)
def detect_anomalies(req: AnomalyRequest, db: Session = Depends(get_db)):
    if db is None:
        return MOCK_ANOMALY
    try:
        from app.models.ihe_models import BankTransaction
        stmt = (
            select(BankTransaction)
            .where(BankTransaction.TransactionDate >= func.dateadd(func.day, -req.days, func.current_date()))
            .order_by(BankTransaction.TransactionID)
        )
        rows = list(db.execute(stmt).scalars().all())
        if not rows:
            return MOCK_ANOMALY
        detector = TransactionAnomalyDetector()
        transactions = [{"amount": float(r.Withdrawal or 0) + float(r.Deposit or 0), "date": str(r.TransactionDate), "narration": r.Narration or ""} for r in rows]
        anomalies = detector.detect(transactions)
        return AnomalyResponse(
            anomaly_count=len(anomalies),
            anomalies=anomalies,
            severity="high" if len(anomalies) > 5 else "medium" if len(anomalies) > 2 else "low",
            source="live"
        )
    except Exception as e:
        return AnomalyResponse(anomaly_count=0, anomalies=[], severity="unknown", source=f"fallback: {e}")
