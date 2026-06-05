#!/usr/bin/env python3
"""
02_bank_loader.py — Load Bnk_TRNX SOURCE.xlsx into dbo.BankTransaction.
Idempotent by composite key (bank_code + transaction_date + amount + narration).
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
DATA_PATH = os.getenv("BANK_DATA_PATH", r"D:\IncentiveHouse_ERP\data\incoming\Bnk_TRNX SOURCE.xlsx")
BATCH_SIZE = 500

BANK_CODE_MAP = {
    "Bnk_Cur": "BNK_CUR",
    "Bnk_Sav": "BNK_SAV",
    "Bnk_Usd": "BNK_USD",
    "Bnk_Eur": "BNK_EUR",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
    return df


def row_exists(session, row: dict) -> bool:
    sql = """
        SELECT 1 FROM dbo.BankTransaction
        WHERE BankCode = :bank_code
          AND TransactionDate = :transaction_date
          AND ABS(ISNULL(Withdrawal, 0) - ISNULL(:withdrawal, 0)) < 0.01
          AND ABS(ISNULL(Deposit, 0) - ISNULL(:deposit, 0)) < 0.01
          AND Narration = :narration
    """
    result = session.execute(text(sql), {
        "bank_code": row.get("bank_code"),
        "transaction_date": row.get("transaction_date"),
        "withdrawal": row.get("withdrawal", 0) or 0,
        "deposit": row.get("deposit", 0) or 0,
        "narration": row.get("narration", ""),
    }).fetchone()
    return result is not None


def insert_rows(session, df: pd.DataFrame) -> tuple:
    inserted, skipped = 0, 0
    for _, row in df.iterrows():
        row_dict = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        if row_exists(session, row_dict):
            skipped += 1
            continue

        row_dict["created_at"] = datetime.now()
        cols = [c for c in row_dict.keys() if row_dict[c] is not None]
        if not cols:
            skipped += 1
            continue
        placeholders = [f":{c}" for c in cols]
        sql = f"INSERT INTO dbo.BankTransaction ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        try:
            session.execute(text(sql), {c: row_dict[c] for c in cols})
            inserted += 1
            if inserted % BATCH_SIZE == 0:
                session.commit()
                print(f"  ... committed {inserted} rows")
        except Exception as e:
            print(f"  [WARN] Skip: {e}")
            skipped += 1
    session.commit()
    return inserted, skipped


def main():
    print("=" * 60)
    print("02_bank_loader.py — Bank Transaction Migration")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    if not os.path.exists(DATA_PATH):
        print(f"[FATAL] File not found: {DATA_PATH}")
        sys.exit(1)

    engine = create_engine(DATABASE_URL, echo=False, future=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    print(f"[READ] {DATA_PATH}")
    df = pd.read_excel(DATA_PATH)
    if df.empty:
        print("[FATAL] Empty file.")
        sys.exit(1)

    df = normalize_columns(df)
    print(f"[INFO] Rows read: {len(df)}")
    print(f"[INFO] Columns: {list(df.columns)}")

    rename_map = {
        "trnx_date": "TransactionDate",
        "date": "TransactionDate",
        "transaction_date": "TransactionDate",
        "payee": "Payee",
        "doc_type": "DocumentType",
        "document_type": "DocumentType",
        "doc_number": "DocumentNumber",
        "document_number": "DocumentNumber",
        "withdrawal": "Withdrawal",
        "withdrawals": "Withdrawal",
        "deposit": "Deposit",
        "deposits": "Deposit",
        "running_balance": "RunningBalance",
        "balance": "RunningBalance",
        "trnx_type": "TransactionType",
        "transaction_type": "TransactionType",
        "type": "TransactionType",
        "jv_number": "JVNumber",
        "jv_no": "JVNumber",
        "narration": "Narration",
        "description": "Narration",
        "dr_account": "DrAccount",
        "cr_account": "CrAccount",
        "from_sub_category": "FromSubCategory",
        "to_sub_category": "ToSubCategory",
        "bank_code": "BankCode",
        "account_code": "BankCode",
        "account": "BankCode",
        "currency_code": "CurrencyCode",
        "currency": "CurrencyCode",
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    required = {"BankCode", "TransactionDate", "Narration"}
    missing = required - set(df.columns)
    if missing:
        print(f"[FATAL] Missing columns: {missing}")
        sys.exit(1)

    ins, skp = insert_rows(session, df)
    session.close()

    print("\n" + "=" * 60)
    print(f"TOTAL Inserted: {ins} | Skipped (exists): {skp}")
    print(f"Finished: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
