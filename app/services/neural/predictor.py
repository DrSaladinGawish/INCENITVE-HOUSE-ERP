import io
import json
import joblib
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestClassifier,
    IsolationForest,
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


class BasePredictor:
    def __init__(self, db: Session | None = None):
        self.db = db
        self.model = None
        self.scaler = None
        self._fitted = False

    def _make_pipeline(self, model) -> Pipeline:
        return Pipeline([("scaler", StandardScaler()), ("model", model)])

    def _validate_fitted(self):
        if not self._fitted or self.model is None:
            self._lazy_fit()

    def _lazy_fit(self):
        X, y = self._build_training_data()
        if X is None or len(X) == 0:
            self._fitted = False
            return
        self._fit(X, y)

    def _fit(self, X: np.ndarray, y: np.ndarray | None = None):
        raise NotImplementedError

    def _build_training_data(self):
        raise NotImplementedError

    def predict(self, **kwargs) -> dict:
        self._validate_fitted()
        return self._predict(**kwargs)

    def _predict(self, **kwargs) -> dict:
        raise NotImplementedError

    def serialize(self) -> bytes:
        buf = io.BytesIO()
        joblib.dump({"model": self.model, "scaler": self.scaler, "fitted": self._fitted}, buf)
        return buf.getvalue()

    def deserialize(self, data: bytes):
        buf = io.BytesIO(data)
        obj = joblib.load(buf)
        self.model = obj["model"]
        self.scaler = obj["scaler"]
        self._fitted = obj["fitted"]


class CashFlowPredictor(BasePredictor):
    def __init__(self, db: Session | None = None, forecast_days: int = 30):
        super().__init__(db)
        self.forecast_days = forecast_days
        self.model = self._make_pipeline(
            GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
        )

    def _build_training_data(self):
        from app.models.ihe_models import BankTransaction
        if not self.db:
            return None, None
        try:
            rows = (
                self.db.execute(
                    select(BankTransaction.TransactionDate, BankTransaction.Deposit, BankTransaction.Withdrawal,
                           BankTransaction.RunningBalance)
                    .order_by(BankTransaction.TransactionDate)
                )
                .all()
            )
        except Exception:
            return None, None
        if len(rows) < 10:
            return None, None
        dates = [r[0] for r in rows]
        deposits = np.array([float(r[1] or 0) for r in rows])
        withdrawals = np.array([float(r[2] or 0) for r in rows])
        balances = np.array([float(r[3] or 0) for r in rows])
        X = []
        y = []
        for i in range(5, len(rows)):
            features = [
                deposits[i - 1], withdrawals[i - 1], balances[i - 1],
                deposits[i - 2], withdrawals[i - 2], balances[i - 2],
                deposits[i - 3], withdrawals[i - 3], balances[i - 3],
                float(dates[i].month), float(dates[i].weekday()),
            ]
            X.append(features)
            y.append(balances[i])
        return np.array(X), np.array(y)

    def _fit(self, X, y):
        self.model.fit(X, y)
        self._fitted = True

    def _predict(self, **kwargs) -> dict:
        from app.models.ihe_models import BankTransaction
        try:
            recent = (
                self.db.execute(
                    select(BankTransaction.Deposit, BankTransaction.Withdrawal, BankTransaction.RunningBalance,
                           BankTransaction.TransactionDate)
                    .order_by(BankTransaction.TransactionDate.desc())
                    .limit(5)
                )
                .all()
            )
        except Exception:
            recent = []
        if len(recent) < 5:
            return {
                "prediction": None,
                "forecast_days": self.forecast_days,
                "confidence": 0.0,
                "trend": "unknown",
                "message": "Insufficient transaction history for cash flow prediction.",
            }
        recent = list(reversed(recent))
        deposits = [float(r[0] or 0) for r in recent]
        withdrawals = [float(r[1] or 0) for r in recent]
        balances = [float(r[2] or 0) for r in recent]
        current_balance = balances[-1]
        avg_deposit = np.mean(deposits)
        avg_withdrawal = np.mean(withdrawals)
        net_flow = avg_deposit - avg_withdrawal
        projected = current_balance + net_flow * self.forecast_days
        trend = "improving" if net_flow > 0 else "declining" if net_flow < 0 else "stable"
        cash_risk = "high" if projected < 0 else "medium" if projected < current_balance * 0.3 else "low"
        X_input = np.array([[
            deposits[-1], withdrawals[-1], balances[-1],
            deposits[-2], withdrawals[-2], balances[-2],
            deposits[-3], withdrawals[-3], balances[-3],
            float(datetime.now().month), float(datetime.now().weekday()),
        ]])
        try:
            ml_pred = float(self.model.predict(X_input)[0])
        except Exception:
            ml_pred = projected
        return {
            "prediction": round(ml_pred, 2),
            "current_balance": round(current_balance, 2),
            "forecast_days": self.forecast_days,
            "net_daily_flow": round(net_flow, 2),
            "trend": trend,
            "cash_risk": cash_risk,
            "confidence": 0.75,
        }


class ClientChurnPredictor(BasePredictor):
    def __init__(self, db: Session | None = None):
        super().__init__(db)
        self.model = self._make_pipeline(
            RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        )

    def _build_training_data(self):
        from app.models.ihe_models import Client, PNRMaster, SalesInvoice
        if not self.db:
            return None, None
        try:
            clients = self.db.execute(select(Client.ClientCode)).all()
        except Exception:
            return None, None
        if len(clients) < 5:
            return None, None
        X, y = [], []
        for (client_code,) in clients:
            try:
                pnr_count = (
                    self.db.execute(
                        select(func.count(PNRMaster.PNRNumber)).where(PNRMaster.ClientCode == client_code)
                    ).scalar() or 0
                )
                active_pnrs = (
                    self.db.execute(
                        select(func.count(PNRMaster.PNRNumber))
                        .where(PNRMaster.ClientCode == client_code, PNRMaster.Status == "Active")
                    ).scalar() or 0
                )
                total_revenue = (
                    self.db.execute(
                        select(func.coalesce(func.sum(SalesInvoice.TotalValue), 0))
                        .where(SalesInvoice.ClientCode == client_code)
                    ).scalar() or 0.0
                )
                unpaid = (
                    self.db.execute(
                        select(func.coalesce(func.sum(SalesInvoice.TotalValue - SalesInvoice.CollectedAmount), 0))
                        .where(SalesInvoice.ClientCode == client_code, SalesInvoice.PaymentStatus != "Paid")
                    ).scalar() or 0.0
                )
            except Exception:
                continue
            features = [float(pnr_count), float(active_pnrs), float(total_revenue), float(unpaid)]
            label = 0 if active_pnrs > 0 else 1
            X.append(features)
            y.append(label)
        return (np.array(X), np.array(y)) if len(X) >= 5 else (None, None)

    def _fit(self, X, y):
        self.model.fit(X, y)
        self._fitted = True

    def _predict(self, client_code: str | None = None, **kwargs) -> dict:
        if not client_code or not self.db:
            return {"prediction": None, "confidence": 0.0, "risk_level": "unknown", "message": "Client code required."}
        from app.models.ihe_models import PNRMaster, SalesInvoice
        try:
            pnr_count = self.db.execute(select(func.count(PNRMaster.PNRNumber)).where(PNRMaster.ClientCode == client_code)).scalar() or 0
            active_pnrs = self.db.execute(select(func.count(PNRMaster.PNRNumber)).where(PNRMaster.ClientCode == client_code, PNRMaster.Status == "Active")).scalar() or 0
            total_revenue = self.db.execute(select(func.coalesce(func.sum(SalesInvoice.TotalValue), 0)).where(SalesInvoice.ClientCode == client_code)).scalar() or 0.0
            unpaid = self.db.execute(select(func.coalesce(func.sum(SalesInvoice.TotalValue - SalesInvoice.CollectedAmount), 0)).where(SalesInvoice.ClientCode == client_code, SalesInvoice.PaymentStatus != "Paid")).scalar() or 0.0
        except Exception:
            return {"prediction": None, "confidence": 0.0, "risk_level": "unknown", "message": "Error querying client data."}
        X_input = np.array([[float(pnr_count), float(active_pnrs), float(total_revenue), float(unpaid)]])
        try:
            prob = float(self.model.predict_proba(X_input)[0][1])
        except Exception:
            prob = 1.0 - (active_pnrs / max(pnr_count, 1)) if pnr_count > 0 else 0.5
        risk_level = "high" if prob > 0.6 else "medium" if prob > 0.3 else "low"
        actions = []
        if risk_level == "high":
            actions.append("Schedule client engagement meeting")
            actions.append("Offer bundled event packages")
        elif risk_level == "medium":
            actions.append("Send quarterly newsletter")
            actions.append("Check satisfaction on recent PNRs")
        return {
            "client_code": client_code,
            "churn_probability": round(prob, 4),
            "risk_level": risk_level,
            "total_pnrs": pnr_count,
            "active_pnrs": active_pnrs,
            "total_revenue": float(total_revenue),
            "recommended_actions": actions,
            "confidence": round(0.5 + 0.3 * (1 - prob), 2),
        }


class PnrOverrunPredictor(BasePredictor):
    def __init__(self, db: Session | None = None):
        super().__init__(db)
        self.model = self._make_pipeline(
            GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
        )

    def _build_training_data(self):
        from app.models.ihe_models import PNRMaster, PurchaseVoucher, PNRBudgetLineItem
        if not self.db:
            return None, None
        try:
            pnrs = self.db.execute(select(PNRMaster.PNRNumber, PNRMaster.Year).where(PNRMaster.PNRNumber.isnot(None))).all()
        except Exception:
            return None, None
        if len(pnrs) < 5:
            return None, None
        X, y = [], []
        for (pnr_number, year) in pnrs:
            try:
                budget_total = self.db.execute(select(func.coalesce(func.sum(PNRBudgetLineItem.Amount), 0)).where(PNRBudgetLineItem.JobFolder == pnr_number)).scalar() or 0.0
                actual_total = self.db.execute(select(func.coalesce(func.sum(PurchaseVoucher.TotalValue), 0)).where(PurchaseVoucher.PNRNumber == pnr_number)).scalar() or 0.0
                line_count = self.db.execute(select(func.count(PNRBudgetLineItem.LineItemID)).where(PNRBudgetLineItem.JobFolder == pnr_number)).scalar() or 0
            except Exception:
                continue
            features = [float(budget_total), float(line_count), float(year or 0)]
            overrun = float(actual_total) - float(budget_total)
            X.append(features)
            y.append(max(overrun, 0))
        return (np.array(X), np.array(y)) if len(X) >= 5 else (None, None)

    def _fit(self, X, y):
        self.model.fit(X, y)
        self._fitted = True

    def _predict(self, pnr_number: str | None = None, **kwargs) -> dict:
        if not pnr_number or not self.db:
            return {"prediction": None, "overrun_pct": None, "confidence": 0.0, "message": "PNR number required."}
        from app.models.ihe_models import PNRBudgetLineItem, PurchaseVoucher, PNRMaster
        try:
            budget_total = self.db.execute(select(func.coalesce(func.sum(PNRBudgetLineItem.Amount), 0)).where(PNRBudgetLineItem.JobFolder == pnr_number)).scalar() or 0.0
            actual_total = self.db.execute(select(func.coalesce(func.sum(PurchaseVoucher.TotalValue), 0)).where(PurchaseVoucher.PNRNumber == pnr_number)).scalar() or 0.0
            line_count = self.db.execute(select(func.count(PNRBudgetLineItem.LineItemID)).where(PNRBudgetLineItem.JobFolder == pnr_number)).scalar() or 0
            year = self.db.execute(select(PNRMaster.Year).where(PNRMaster.PNRNumber == pnr_number)).scalar() or datetime.now().year
        except Exception:
            return {"prediction": None, "overrun_pct": None, "confidence": 0.0, "message": "Error querying PNR data."}
        X_input = np.array([[float(budget_total), float(line_count), float(year)]])
        try:
            predicted_overrun = float(self.model.predict(X_input)[0])
        except Exception:
            predicted_overrun = max(0, float(actual_total) - float(budget_total))
        overrun_pct = (predicted_overrun / max(float(budget_total), 1)) * 100
        risk_level = "high" if overrun_pct > 20 else "medium" if overrun_pct > 10 else "low"
        mitigations = []
        if risk_level == "high":
            mitigations.append("Review budget line items for cost reduction")
            mitigations.append("Negotiate vendor rates")
            mitigations.append("Consolidate service categories")
        elif risk_level == "medium":
            mitigations.append("Monitor top 3 expense categories")
            mitigations.append("Set weekly budget review")
        return {
            "pnr_number": pnr_number,
            "budget_total": float(budget_total),
            "actual_spent": float(actual_total),
            "predicted_final_cost": round(float(budget_total) + predicted_overrun, 2),
            "predicted_overrun": round(predicted_overrun, 2),
            "overrun_percentage": round(overrun_pct, 2),
            "risk_level": risk_level,
            "mitigation_actions": mitigations,
            "confidence": 0.7,
        }


class TransactionAnomalyDetector(BasePredictor):
    def __init__(self, db: Session | None = None, contamination: float = 0.1):
        super().__init__(db)
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("detector", IsolationForest(contamination=contamination, random_state=42, n_estimators=100)),
        ])

    def _build_training_data(self):
        from app.models.ihe_models import BankTransaction
        if not self.db:
            return None, None
        try:
            rows = self.db.execute(
                select(BankTransaction.Withdrawal, BankTransaction.Deposit, BankTransaction.RunningBalance)
                .limit(1000)
            ).all()
        except Exception:
            return None, None
        if len(rows) < 10:
            return None, None
        X = np.array([[float(r[0] or 0), float(r[1] or 0), float(r[2] or 0)] for r in rows])
        return X, None

    def _fit(self, X, y=None):
        self.model.fit(X)
        self._fitted = True

    def _predict(self, transaction_ids: list[int] | None = None, **kwargs) -> dict:
        from app.models.ihe_models import BankTransaction
        if not self.db:
            return {"anomalies": [], "total_analyzed": 0, "message": "No database connection."}
        try:
            stmt = select(BankTransaction)
            if transaction_ids:
                stmt = stmt.where(BankTransaction.TransactionID.in_(transaction_ids))
            rows = self.db.execute(stmt.order_by(BankTransaction.TransactionDate.desc()).limit(200)).scalars().all()
        except Exception:
            return {"anomalies": [], "total_analyzed": 0, "message": "Error querying transactions."}
        if len(rows) < 5:
            return {"anomalies": [], "total_analyzed": 0, "message": "Insufficient transactions for anomaly detection."}
        X = np.array([[float(r.Withdrawal or 0), float(r.Deposit or 0), float(r.RunningBalance or 0)] for r in rows])
        try:
            scores = self.model.decision_function(X)
            predictions = self.model.predict(X)
        except Exception:
            return {"anomalies": [], "total_analyzed": len(rows), "message": "Model not fitted."}
        anomalies = []
        for i, (tx, pred, score) in enumerate(zip(rows, predictions, scores)):
            if pred == -1:
                anomalies.append({
                    "transaction_id": tx.TransactionID,
                    "date": str(tx.TransactionDate),
                    "payee": tx.Payee,
                    "withdrawal": float(tx.Withdrawal or 0),
                    "deposit": float(tx.Deposit or 0),
                    "anomaly_score": round(float(score), 4),
                    "reason": _anomaly_reason(tx, X[i]),
                })
        return {
            "anomalies": anomalies,
            "total_analyzed": len(rows),
            "anomaly_count": len(anomalies),
            "anomaly_rate": round(len(anomalies) / max(len(rows), 1), 4),
            "message": f"Found {len(anomalies)} anomalies in {len(rows)} transactions.",
        }


def _anomaly_reason(tx, features) -> str:
    reasons = []
    w, d, b = features
    if w > 0 and w > b * 0.5 and b > 0:
        reasons.append("Withdrawal exceeds 50% of balance")
    if d > 0 and d > np.mean([f[1] for f in [features]]) * 3 if len(features.shape) > 1 else True:
        reasons.append("Deposit unusually large")
    if b < 0:
        reasons.append("Negative balance")
    return "; ".join(reasons[:2]) if reasons else "Statistical outlier"
