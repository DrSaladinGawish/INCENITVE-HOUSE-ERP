#!/usr/bin/env python3
"""
99_rollback.py — Emergency rollback with backup table creation.
Creates .bak tables before truncating. Supports selective or full rollback.
"""

import os
import sys
import argparse
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", (
    "mssql+pyodbc://sa:YourStrong@Passw0rd@localhost/IHE_ERP"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
))

TABLES = [
    "dbo.Currency", "dbo.Client", "dbo.Vendor", "dbo.Employee", "dbo.Bank",
    "dbo.ServiceMainCategory", "dbo.ServiceSubCategory", "dbo.ServiceType",
    "dbo.ChartOfAccounts", "dbo.PNRMaster", "dbo.ClientEmployee",
    "dbo.PNRBudgetLineItem", "dbo.SalesInvoice", "dbo.SalesInvoiceLine",
    "dbo.PurchaseVoucher", "dbo.PurchaseVoucherLine", "dbo.BankTransaction",
    "dbo.JournalVoucher", "dbo.JournalVoucherLine",
    "dbo.SupportingDocument", "dbo.DocumentModule",
    "dbo.NeuralNode", "dbo.NeuralPrediction", "dbo.NeuralFeatureStore",
    "dbo.NeuralTrainingHistory", "dbo.NeuralMemory",
]


def backup_table(conn, table: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak_name = f"{table.split('.')[-1]}_bak_{ts}"
    conn.execute(text(f"SELECT * INTO dbo.{bak_name} FROM {table}"))
    conn.commit()
    print(f"  [BACKUP] {table} -> dbo.{bak_name}")
    return bak_name


def truncate_table(conn, table: str):
    conn.execute(text(f"ALTER TABLE {table} NOCHECK CONSTRAINT ALL"))
    try:
        conn.execute(text(f"TRUNCATE TABLE {table}"))
    except Exception:
        conn.execute(text(f"DELETE FROM {table}"))
    conn.execute(text(f"ALTER TABLE {table} CHECK CONSTRAINT ALL"))
    conn.commit()
    print(f"  [TRUNC] {table}")


def main():
    parser = argparse.ArgumentParser(description="IHE-ERP Migration Rollback")
    parser.add_argument("--full", action="store_true", help="Rollback ALL tables")
    parser.add_argument("--tables", nargs="+", help="Rollback specific tables")
    parser.add_argument("--keep-backup", action="store_true", help="Keep SQL backup tables")
    args = parser.parse_args()

    print("=" * 60)
    print("99_rollback.py — Emergency Rollback")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    engine = create_engine(DATABASE_URL, echo=False, future=True)
    conn = engine.connect()

    target_tables = args.tables if args.tables else (TABLES if args.full else [])
    if not target_tables:
        print("[FATAL] No tables specified. Use --full or --tables")
        sys.exit(1)

    bak_log = []
    for table in target_tables:
        try:
            bak = backup_table(conn, table)
            bak_log.append((table, bak))
            truncate_table(conn, table)
        except Exception as e:
            print(f"  [ERROR] {table}: {e}")
            conn.rollback()

    if not args.keep_backup:
        print("\n[INFO] Backup tables remain. Drop manually when confident:")
        for _, bak in bak_log:
            print(f"  DROP TABLE dbo.{bak};")

    conn.close()
    print("\n" + "=" * 60)
    print(f"Rollback complete. {len(bak_log)} tables truncated.")
    print(f"Finished: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
