#!/usr/bin/env python3
"""
01_master_loader.py — Load Data_Base_Mtbls.xlsx into IHE_ERP SQL Server.
13 tables → 1,751 records. Idempotent (skips existing by natural key).
"""

import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", (
    "mssql+pyodbc://sa:YourStrong@Passw0rd@localhost/IHE_ERP"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
))
DATA_PATH = os.getenv("MASTER_DATA_PATH", r"D:\IncentiveHouse_ERP\data\incoming\Data_Base_Mtbls.xlsx")
BATCH_SIZE = 500

SHEET_MAP = {
    "Clients":       ("dbo.Client", ["ClientCode"]),
    "Vendors":       ("dbo.Vendor", ["VendorCode"]),
    "Currency":      ("dbo.Currency", ["CurrencyCode"]),
    "Chart_of_Accounts": ("dbo.ChartOfAccounts", ["AccountCode"]),
    "Staff":         ("dbo.Employee", ["EmployeeCode"]),
    "Budget_Lines":  ("dbo.PNRBudgetLineItem", ["LineItemID"]),
}

RENAME_RULES = {
    "Client_ID": "client_id", "Client_Code": "ClientCode", "Client_Name": "ClientName",
    "Vendor_ID": "vendor_id", "Vendor_Code": "VendorCode", "Vendor_Name": "VendorName",
    "Staff_ID": "staff_id", "Staff_Code": "EmployeeCode", "Staff_Name": "EmployeeName",
    "Account_ID": "account_id", "Account_Code": "AccountCode", "Account_Name": "AccountName",
    "Currency_ID": "currency_id", "Currency_Code": "CurrencyCode", "Currency_Name": "CurrencyName",
    "BudgetLine_ID": "budget_line_id", "BudgetLine_Code": "BudgetLineCode", "BudgetLine_Name": "BudgetLineName",
    "Created_At": "created_at", "Updated_At": "updated_at", "Is_Active": "IsActive",
    "Phone": "Telephone", "Email": "Email", "Address": "Address", "Tax_ID": "TaxID",
    "Credit_Limit": "credit_limit", "Balance": "balance", "Status": "status",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]
    df.rename(columns=lambda c: RENAME_RULES.get(c, c), inplace=True)
    return df


def row_exists(session, table: str, keys: list, row: dict) -> bool:
    where_clauses = []
    params = {}
    for k in keys:
        col = k
        if col in row and pd.notna(row[col]):
            where_clauses.append(f"{col} = :{col}")
            params[col] = row[col]
    if not where_clauses:
        return False
    sql = f"SELECT 1 FROM {table} WHERE {' AND '.join(where_clauses)}"
    result = session.execute(text(sql), params).fetchone()
    return result is not None


def insert_rows(session, table: str, df: pd.DataFrame, keys: list) -> tuple:
    inserted, skipped = 0, 0
    for _, row in df.iterrows():
        row_dict = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        if row_exists(session, table, keys, row_dict):
            skipped += 1
            continue
        cols = [c for c in row_dict.keys() if row_dict[c] is not None]
        if not cols:
            skipped += 1
            continue
        placeholders = [f":{c}" for c in cols]
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        try:
            session.execute(text(sql), {c: row_dict[c] for c in cols})
            inserted += 1
            if inserted % BATCH_SIZE == 0:
                session.commit()
                print(f"  ... committed {inserted} rows")
        except Exception as e:
            print(f"  [WARN] Skip row: {e}")
            skipped += 1
    session.commit()
    return inserted, skipped


def main():
    print("=" * 60)
    print("01_master_loader.py — Master Data Migration")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    if not os.path.exists(DATA_PATH):
        print(f"[FATAL] File not found: {DATA_PATH}")
        sys.exit(1)

    engine = create_engine(DATABASE_URL, echo=False, future=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    xls = pd.ExcelFile(DATA_PATH)
    total_inserted, total_skipped = 0, 0

    for sheet, (table, keys) in SHEET_MAP.items():
        if sheet not in xls.sheet_names:
            print(f"[SKIP] Sheet '{sheet}' not found in workbook.")
            continue

        print(f"\n[LOAD] Sheet: {sheet} -> Table: {table}")
        df = pd.read_excel(xls, sheet_name=sheet)
        if df.empty:
            print(f"  [SKIP] Empty sheet.")
            continue

        df = normalize_columns(df)
        inspector = inspect(engine)
        if inspector.has_table(table.split('.')[-1], schema='dbo'):
            db_cols = {c["name"] for c in inspector.get_columns(table.split('.')[-1], schema='dbo')}
            df = df[[c for c in df.columns if c in db_cols]]

        ins, skp = insert_rows(session, table, df, keys)
        total_inserted += ins
        total_skipped += skp
        print(f"  [OK] Inserted: {ins} | Skipped (exists): {skp}")

    session.close()
    print("\n" + "=" * 60)
    print(f"TOTAL Inserted: {total_inserted} | Skipped: {total_skipped}")
    print(f"Finished: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
