#!/usr/bin/env python3
"""
03_gl_loader.py — Load Gen_Led CSVs into dbo.JournalVoucher + dbo.JournalVoucherLine.
Sources: Gen_Led_Bnk.csv, Gen_Led_SAL.csv, Gen_Led_PUR.csv
Creates journal vouchers from general ledger CSV exports.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", (
    "mssql+pyodbc://sa:YourStrong@Passw0rd@localhost/IHE_ERP"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
))
DATA_DIR = os.getenv("GENLED_DIR", r"D:\IncentiveHouse_ERP\data\incoming")
BATCH_SIZE = 500

FILES = {
    "Bank":    ("Gen_Led_Bnk.csv", "BNK"),
    "Sales":   ("Gen_Led_SAL.csv", "SAL"),
    "Purchase":("Gen_Led_PUR.csv", "PUR"),
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
    return df


def resolve_account_code(row: dict, module: str) -> str:
    acc = str(row.get("account_code", "") or "")
    if not acc:
        if module == "BNK":
            acc = "BANK_GL"
        elif module == "SAL":
            acc = "SALES_GL"
        elif module == "PUR":
            acc = "PURCHASE_GL"
    return acc


def resolve_jv_number(row: dict, module: str) -> str:
    jv = str(row.get("journal_no", "") or "")
    if not jv:
        ref = str(row.get("reference_no", "") or "")
        dt = str(row.get("movement_date", "") or datetime.now().strftime("%Y%m%d"))
        jv = f"GL-{module}-{dt}"
    return jv


def insert_jv(session, df: pd.DataFrame, module: str) -> int:
    inserted = 0
    for _, row in df.iterrows():
        row_dict = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        account_code = resolve_account_code(row_dict, module)
        jv_number = resolve_jv_number(row_dict, module)
        dt = row_dict.get("movement_date") or datetime.now()
        narration = str(row_dict.get("description", "") or "")

        stmt = text("SELECT 1 FROM dbo.JournalVoucher WHERE JVNumber = :jv")
        exists = session.execute(stmt, {"jv": jv_number}).fetchone()

        debit = float(row_dict.get("debit_amount", 0) or 0)
        credit = float(row_dict.get("credit_amount", 0) or 0)

        if not exists:
            sql_jv = """
                INSERT INTO dbo.JournalVoucher (JVNumber, JVDate, Narration, TotalDebit, TotalCredit)
                VALUES (:jv, :dt, :narration, :debit, :credit)
            """
            try:
                session.execute(text(sql_jv), {
                    "jv": jv_number, "dt": dt, "narration": narration,
                    "debit": debit, "credit": credit,
                })
            except Exception as e:
                print(f"  [WARN] JV insert: {e}")
                continue

        sql_line = """
            INSERT INTO dbo.JournalVoucherLine (JVNumber, AccountCode, DebitAmount, CreditAmount, Narration)
            VALUES (:jv, :acct, :debit, :credit, :narration)
        """
        try:
            session.execute(text(sql_line), {
                "jv": jv_number, "acct": account_code,
                "debit": debit, "credit": credit, "narration": narration,
            })
            inserted += 1
            if inserted % BATCH_SIZE == 0:
                session.commit()
                print(f"  ... committed {inserted} lines")
        except Exception as e:
            print(f"  [WARN] JV line insert: {e}")
    session.commit()
    return inserted


def main():
    print("=" * 60)
    print("03_gl_loader.py — GL Journal Voucher Migration")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    engine = create_engine(DATABASE_URL, echo=False, future=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    total_inserted = 0
    for label, (filename, module) in FILES.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            print(f"[SKIP] {filename} not found.")
            continue

        print(f"\n[LOAD] {label}: {filename}")
        df = pd.read_csv(path, encoding="utf-8-sig")
        print(f"  [INFO] Rows: {len(df)} | Columns: {list(df.columns)}")
        df = normalize_columns(df)
        count = insert_jv(session, df, module)
        total_inserted += count
        print(f"  [OK] Inserted {count} JV lines for {label}")

    session.close()
    print("\n" + "=" * 60)
    print(f"TOTAL JV Lines inserted: {total_inserted}")
    print(f"Finished: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
