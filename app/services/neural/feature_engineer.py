from datetime import datetime, timezone
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session


class FeatureEngineer:
    def __init__(self, db: Session):
        self.db = db

    def refresh_feature_store(self) -> dict:
        results = {}
        results["cash_flow_features"] = self._build_cash_flow_features()
        results["client_features"] = self._build_client_features()
        results["pnr_features"] = self._build_pnr_features()
        results["global_features"] = self._build_global_features()
        return results

    def _build_cash_flow_features(self) -> dict:
        from app.models.ihe_models import BankTransaction
        try:
            total_deposits = self.db.execute(
                select(func.coalesce(func.sum(BankTransaction.Deposit), 0))
            ).scalar() or 0.0
            total_withdrawals = self.db.execute(
                select(func.coalesce(func.sum(BankTransaction.Withdrawal), 0))
            ).scalar() or 0.0
            tx_count = self.db.execute(
                select(func.count(BankTransaction.TransactionID))
            ).scalar() or 0
            last_balance = self.db.execute(
                select(BankTransaction.RunningBalance)
                .order_by(BankTransaction.TransactionID.desc())
                .limit(1)
            ).scalar() or 0.0
            return {
                "total_deposits": float(total_deposits),
                "total_withdrawals": float(total_withdrawals),
                "net_flow": float(total_deposits) - float(total_withdrawals),
                "transaction_count": tx_count,
                "latest_balance": float(last_balance),
            }
        except Exception as e:
            return {"error": str(e)}

    def _build_client_features(self) -> dict:
        from app.models.ihe_models import Client, PNRMaster, SalesInvoice
        try:
            total_clients = self.db.execute(
                select(func.count(Client.ClientCode))
            ).scalar() or 0
            active_pnrs = self.db.execute(
                select(func.count(PNRMaster.PNRNumber)).where(PNRMaster.Status == "Active")
            ).scalar() or 0
            total_revenue = self.db.execute(
                select(func.coalesce(func.sum(SalesInvoice.TotalValue), 0))
            ).scalar() or 0.0
            unpaid = self.db.execute(
                select(func.coalesce(func.sum(SalesInvoice.TotalValue - SalesInvoice.CollectedAmount), 0))
                .where(SalesInvoice.PaymentStatus != "Paid")
            ).scalar() or 0.0
            clients_with_activity = self.db.execute(
                select(func.count(func.distinct(PNRMaster.ClientCode)))
            ).scalar() or 0
            return {
                "total_clients": total_clients,
                "active_pnrs": active_pnrs,
                "total_revenue": float(total_revenue),
                "unpaid_receivables": float(unpaid),
                "clients_with_activity": clients_with_activity,
                "engagement_rate": round(clients_with_activity / max(total_clients, 1), 4),
            }
        except Exception as e:
            return {"error": str(e)}

    def _build_pnr_features(self) -> dict:
        from app.models.ihe_models import PNRMaster, PurchaseVoucher, PNRBudgetLineItem
        try:
            total_pnrs = self.db.execute(
                select(func.count(PNRMaster.PNRNumber))
            ).scalar() or 0
            active_pnrs = self.db.execute(
                select(func.count(PNRMaster.PNRNumber)).where(PNRMaster.Status == "Active")
            ).scalar() or 0
            avg_budget = self.db.execute(
                select(func.coalesce(func.avg(PNRBudgetLineItem.Amount), 0))
            ).scalar() or 0.0
            avg_spend = self.db.execute(
                select(func.coalesce(func.avg(PurchaseVoucher.TotalValue), 0))
                .where(PurchaseVoucher.PNRNumber.isnot(None))
            ).scalar() or 0.0
            return {
                "total_pnrs": total_pnrs,
                "active_pnrs": active_pnrs,
                "average_budget": float(avg_budget),
                "average_spend": float(avg_spend),
                "overrun_rate": round(max(0, float(avg_spend) - float(avg_budget)) / max(float(avg_budget), 1) * 100, 2),
            }
        except Exception as e:
            return {"error": str(e)}

    def _build_global_features(self) -> dict:
        from app.models.ihe_models import Client, Vendor, Currency
        try:
            return {
                "total_clients": self.db.execute(select(func.count(Client.ClientCode))).scalar() or 0,
                "total_vendors": self.db.execute(select(func.count(Vendor.VendorCode))).scalar() or 0,
                "currencies": self.db.execute(select(func.count(Currency.CurrencyCode))).scalar() or 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}
