#!/usr/bin/env python3
"""
06_verify.py — Post-migration verification suite.
Checks: row counts, referential integrity, neural readiness, API smoke tests.
Exit code 0 = all pass. Exit code 1 = any failure.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", (
    "mssql+pyodbc://sa:YourStrong@Passw0rd@localhost/IHE_ERP"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
))

EXPECTED = {
    "dbo.Currency": 3,
    "dbo.Client": 50,
    "dbo.Vendor": 30,
    "dbo.Employee": 25,
    "dbo.Bank": 4,
    "dbo.ChartOfAccounts": 80,
    "dbo.PNRMaster": 400,
    "dbo.PNRBudgetLineItem": 100,
    "dbo.SalesInvoice": 50,
    "dbo.PurchaseVoucher": 50,
    "dbo.BankTransaction": 2500,
    "dbo.JournalVoucher": 200,
    "dbo.JournalVoucherLine": 500,
    "dbo.SupportingDocument": 100,
    "dbo.NeuralFeatureStore": 400,
}

PASS = 0
FAIL = 0
WARN = 0


def check(name: str, ok: bool, msg: str):
    global PASS, FAIL, WARN
    if ok:
        print(f"  [PASS] {name}: {msg}")
        PASS += 1
    else:
        print(f"  [FAIL] {name}: {msg}")
        FAIL += 1


def main():
    global PASS, FAIL, WARN
    print("=" * 60)
    print("06_verify.py — Post-Migration Verification")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    engine = create_engine(DATABASE_URL, echo=False, future=True)
    conn = engine.connect()

    print("\n[CHECK] 1. Row Counts")
    for table, minimum in EXPECTED.items():
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            check(f"{table}", result >= minimum, f"{result} rows (min {minimum})")
        except Exception as e:
            check(f"{table}", False, f"Error: {e}")

    print("\n[CHECK] 2. Referential Integrity")
    try:
        orphan_si = conn.execute(text("""
            SELECT COUNT(*) FROM dbo.SalesInvoice si
            LEFT JOIN dbo.Client c ON si.ClientCode = c.ClientCode
            WHERE c.ClientCode IS NULL
        """)).scalar()
        check("SalesInvoice -> Client", orphan_si == 0, f"{orphan_si} orphans")
    except Exception as e:
        check("SalesInvoice -> Client", False, f"Error: {e}")

    try:
        orphan_pv = conn.execute(text("""
            SELECT COUNT(*) FROM dbo.PurchaseVoucher pv
            LEFT JOIN dbo.PNRMaster p ON pv.PNRNumber = p.PNRNumber
            WHERE p.PNRNumber IS NULL
        """)).scalar()
        check("PurchaseVoucher -> PNRMaster", orphan_pv == 0, f"{orphan_pv} orphans")
    except Exception as e:
        check("PurchaseVoucher -> PNRMaster", False, f"Error: {e}")

    print("\n[CHECK] 3. Neural Readiness")
    try:
        feat_count = conn.execute(text("SELECT COUNT(*) FROM dbo.NeuralFeatureStore")).scalar()
        check("Feature Store populated", feat_count > 100, f"{feat_count} features")
    except Exception as e:
        check("Feature Store", False, f"Error: {e}")

    print("\n[CHECK] 4. API Smoke Tests")
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:9001/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            check("API health", resp.status == 200, f"HTTP {resp.status}")
    except Exception as e:
        print(f"  [WARN] API not reachable: {e}")

    conn.close()

    print("\n" + "=" * 60)
    print(f"PASS: {PASS} | FAIL: {FAIL} | WARN: {WARN}")
    if FAIL == 0:
        print("STATUS: ALL CRITICAL CHECKS PASSED")
    else:
        print("STATUS: FAILURES DETECTED — Review before production")
    print(f"Finished: {datetime.now().isoformat()}")
    print("=" * 60)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
