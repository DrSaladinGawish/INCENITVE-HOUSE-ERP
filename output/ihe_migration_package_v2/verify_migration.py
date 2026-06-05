#!/usr/bin/env python3
"""
verify_migration.py — Post-migration database state verification.
Checks row counts across 10 key tables. Exit 0 = all pass.
"""

import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", (
    "mssql+pyodbc://sa:YourStrong@Passw0rd@localhost/IHE_ERP"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
))

CHECKS = [
    ("SELECT COUNT(*) FROM dbo.Client", "Clients"),
    ("SELECT COUNT(*) FROM dbo.Vendor", "Vendors"),
    ("SELECT COUNT(*) FROM dbo.PNRMaster", "PNRs"),
    ("SELECT COUNT(*) FROM dbo.BankTransaction", "Bank Transactions"),
    ("SELECT COUNT(*) FROM dbo.SalesInvoice", "Sales Invoices"),
    ("SELECT COUNT(*) FROM dbo.PurchaseVoucher", "Purchase Vouchers"),
    ("SELECT COUNT(*) FROM dbo.JournalVoucher", "Journal Vouchers"),
    ("SELECT COUNT(*) FROM dbo.JournalVoucherLine", "JV Lines"),
    ("SELECT COUNT(*) FROM dbo.NeuralFeatureStore", "Neural Features"),
    ("SELECT COUNT(*) FROM dbo.SupportingDocument", "Documents"),
]

PASS = 0
FAIL = 0


def main():
    global PASS, FAIL
    print("\n[VERIFICATION] Post-Migration Database State")
    print("=" * 55)

    try:
        engine = create_engine(DATABASE_URL, echo=False, future=True)
        conn = engine.connect()

        total = 0
        for query, label in CHECKS:
            try:
                count = conn.execute(text(query)).scalar() or 0
                total += count
                status = f"{count:>8,} records"
                print(f"  [PASS] {label:.<30} {status}")
                PASS += 1
            except Exception as e:
                print(f"  [FAIL] {label:.<30} ERROR: {e}")
                FAIL += 1

        print("=" * 55)
        print(f"  {'TOTAL':.<30} {total:>8,} records")
        conn.close()

    except Exception as e:
        print(f"  [FATAL] Connection error: {e}")
        FAIL += 1

    print(f"\nPASS: {PASS} | FAIL: {FAIL}")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
