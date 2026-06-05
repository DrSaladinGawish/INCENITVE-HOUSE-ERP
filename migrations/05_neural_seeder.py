#!/usr/bin/env python3
"""
05_neural_seeder.py — Populate dbo.NeuralFeatureStore from loaded production data.
CashFlow, Engagement, Overrun, Anomaly features. Idempotent (clear + re-insert).
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", (
    "mssql+pyodbc://sa:YourStrong@Passw0rd@localhost/IHE_ERP"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
))
BATCH_SIZE = 500


def clear_and_insert(session, feature_name: str, rows: list) -> int:
    session.execute(
        text("DELETE FROM dbo.NeuralFeatureStore WHERE FeatureName = :fn"),
        {"fn": feature_name}
    )
    session.commit()
    inserted = 0
    for row in rows:
        cols = [c for c in row.keys() if row[c] is not None]
        placeholders = [f":{c}" for c in cols]
        sql = f"INSERT INTO dbo.NeuralFeatureStore ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        try:
            session.execute(text(sql), row)
            inserted += 1
            if inserted % BATCH_SIZE == 0:
                session.commit()
        except Exception as e:
            print(f"  [WARN] Skip feature: {e}")
    session.commit()
    return inserted


def extract_cashflow(session) -> list:
    print("[EXTRACT] CashFlow features...")
    try:
        result = session.execute(text("""
            SELECT
                CAST(TransactionDate AS DATE) AS dt,
                BankCode,
                SUM(ISNULL(Deposit, 0)) AS total_deposit,
                SUM(ISNULL(Withdrawal, 0)) AS total_withdrawal,
                SUM(ISNULL(Deposit, 0) - ISNULL(Withdrawal, 0)) AS net_amount,
                COUNT(*) AS tx_count
            FROM dbo.BankTransaction
            GROUP BY CAST(TransactionDate AS DATE), BankCode
            ORDER BY dt
        """)).fetchall()
    except Exception as e:
        print(f"  [WARN] Cashflow query failed: {e}")
        return []

    rows = []
    for r in result:
        rows.append({
            "EntityType": "account",
            "EntityID": hash(str(r.BankCode)) % 1000000,
            "FeatureName": "cashflow_daily",
            "FeatureValue": float(r.net_amount),
            "FeatureData": str({
                "total_deposit": float(r.total_deposit),
                "total_withdrawal": float(r.total_withdrawal),
                "tx_count": int(r.tx_count),
            }),
            "ComputedAt": datetime.now(),
        })
    return rows


def extract_churn(session) -> list:
    print("[EXTRACT] Engagement features...")
    try:
        result = session.execute(text("""
            SELECT
                c.ClientCode,
                COUNT(DISTINCT si.InvoiceID) AS invoice_count,
                COALESCE(SUM(si.TotalValue), 0) AS total_revenue,
                COALESCE(MAX(si.InvoiceDate), '1900-01-01') AS last_invoice_date
            FROM dbo.Client c
            LEFT JOIN dbo.SalesInvoice si ON c.ClientCode = si.ClientCode
            GROUP BY c.ClientCode
        """)).fetchall()
    except Exception as e:
        print(f"  [WARN] Engagement query failed: {e}")
        return []

    rows = []
    for r in result:
        rows.append({
            "EntityType": "client",
            "EntityID": hash(str(r.ClientCode)) % 1000000,
            "FeatureName": "client_engagement",
            "FeatureValue": float(r.total_revenue),
            "FeatureData": str({
                "invoice_count": int(r.invoice_count),
                "last_invoice_date": str(r.last_invoice_date),
            }),
            "ComputedAt": datetime.now(),
        })
    return rows


def extract_overrun(session) -> list:
    print("[EXTRACT] Overrun features...")
    try:
        result = session.execute(text("""
            SELECT
                p.PNRNumber,
                COALESCE(SUM(b.Amount), 0) AS total_budget,
                COALESCE(SUM(pv.TotalValue), 0) AS total_actual
            FROM dbo.PNRMaster p
            LEFT JOIN dbo.PNRBudgetLineItem b ON p.PNRNumber = b.JobFolder
            LEFT JOIN dbo.PurchaseVoucher pv ON p.PNRNumber = pv.PNRNumber
            GROUP BY p.PNRNumber
        """)).fetchall()
    except Exception as e:
        print(f"  [WARN] Overrun query failed: {e}")
        return []

    rows = []
    for r in result:
        budget = float(r.total_budget)
        actual = float(r.total_actual)
        overrun_pct = ((actual - budget) / budget * 100) if budget > 0 else 0
        rows.append({
            "EntityType": "pnr",
            "EntityID": hash(str(r.PNRNumber)) % 1000000,
            "FeatureName": "pnr_budget_actual",
            "FeatureValue": overrun_pct,
            "FeatureData": str({
                "total_budget": budget,
                "total_actual": actual,
                "overrun_pct": overrun_pct,
            }),
            "ComputedAt": datetime.now(),
        })
    return rows


def main():
    print("=" * 60)
    print("05_neural_seeder.py — Neural Feature Store Seeder")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    engine = create_engine(DATABASE_URL, echo=False, future=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    total = 0

    rows = extract_cashflow(session)
    total += clear_and_insert(session, "cashflow_daily", rows)
    print(f"  [OK] CashFlow: {len(rows)} features")

    rows = extract_churn(session)
    total += clear_and_insert(session, "client_engagement", rows)
    print(f"  [OK] Engagement: {len(rows)} features")

    rows = extract_overrun(session)
    total += clear_and_insert(session, "pnr_budget_actual", rows)
    print(f"  [OK] Overrun: {len(rows)} features")

    session.close()
    print("\n" + "=" * 60)
    print(f"TOTAL Features inserted: {total}")
    print(f"Finished: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
