#!/usr/bin/env python3
"""Extraction Engine v2.2 — Production-Ready"""

import os
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

import pandas as pd
import numpy as np

DB_FILE = os.environ.get("DB_FILE", "protocell_staging.db")
SOURCE_DIR = os.environ.get("XLSX_SOURCE_DIR", ".")
SOURCE_PATHS = ["", SOURCE_DIR, "."]

logger = logging.getLogger("extraction_engine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def resolve_source_file(filename: str) -> str:
    for base in SOURCE_PATHS:
        full = Path(base) / filename if base else Path(filename)
        if full.exists():
            return str(full)
    return filename

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_table_counts() -> Dict[str, int]:
    with get_db() as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        counts = {}
        for table in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                counts[table] = count
            except Exception as e:
                counts[table] = f"ERROR: {e}"
        return counts

MASTER_TABLE_MAP = {
    "COA": "coa_master", "COA_Mtble": "coa_master",
    "Clients": "client_master", "Clnt_Mtbl": "client_master",
    "Vendors": "vendor_master", "Sup_Mtbl": "vendor_master",
    "Staff": "staff_master", "Stff_Mtbl": "staff_master",
    "Items": "item_master", "Events": "event_master",
    "Suppliers": "supplier_master", "BudgetLines": "budget_line_master",
    "Branches": "branch_master", "Currencies": "currency_master",
    "PaymentTerms": "payment_term_master", "Departments": "department_master",
    "CostCenters": "cost_center_master",
}

def _resolve_master_table(sheet_name: str) -> Optional[str]:
    if sheet_name in MASTER_TABLE_MAP:
        return MASTER_TABLE_MAP[sheet_name]
    for key, val in MASTER_TABLE_MAP.items():
        if key.lower() == sheet_name.lower():
            return val
    for key, val in MASTER_TABLE_MAP.items():
        if key.lower() in sheet_name.lower() or sheet_name.lower() in key.lower():
            return val
    return None

def extract_master_data(source_file: str = "Data_Base_Mtbls.xlsx") -> Dict[str, Any]:
    results = {"status": "SUCCESS", "tables_processed": 0, "records_inserted": 0, "errors": [], "details": {}}
    resolved = resolve_source_file(source_file)
    try:
        xls = pd.ExcelFile(resolved)
    except FileNotFoundError:
        results["status"] = "ERROR"
        results["errors"].append(f"File not found: {resolved}")
        return results
    except Exception as e:
        results["status"] = "ERROR"
        results["errors"].append(f"Error opening Excel: {str(e)}")
        return results
    
    batch_id = f"master_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with get_db() as conn:
        for sheet_name in xls.sheet_names:
            table_name = _resolve_master_table(sheet_name)
            if not table_name:
                results["details"][sheet_name] = {"status": "SKIPPED", "reason": "No table mapping"}
                continue
            
            try:
                df = None
                for header_row in range(3):
                    try:
                        df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
                        if len(df.columns) >= 2 and not all(str(c).startswith("Unnamed") for c in df.columns):
                            break
                    except Exception:
                        continue
                
                if df is None or df.empty:
                    results["details"][sheet_name] = {"status": "EMPTY", "records": 0}
                    continue
                
                df.columns = [str(c).strip().replace(" ", "_").replace("-", "_") for c in df.columns]
                df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
                
                if df.empty:
                    results["details"][sheet_name] = {"status": "EMPTY_AFTER_CLEAN", "records": 0}
                    continue
                
                df["_extracted_at"] = datetime.now().isoformat()
                df["_source_file"] = source_file
                df["_batch_id"] = batch_id
                
                cols = df.columns.tolist()
                col_defs = ", ".join([f'"{c}" TEXT' for c in cols])
                create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (id INTEGER PRIMARY KEY AUTOINCREMENT, {col_defs})'
                conn.execute(create_sql)
                
                placeholders = ", ".join(["?"] * len(cols))
                col_names = ", ".join([f'"{c}"' for c in cols])
                insert_sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'
                
                records = []
                for _, row in df.iterrows():
                    records.append(tuple(str(v) if pd.notna(v) else None for v in row.values))
                
                if records:
                    conn.executemany(insert_sql, records)
                    conn.commit()
                    results["tables_processed"] += 1
                    results["records_inserted"] += len(records)
                    results["details"][sheet_name] = {
                        "status": "SUCCESS", "records": len(records), "table": table_name, "header_row": header_row
                    }
                    logger.info(f"Master: {sheet_name} -> {table_name}: {len(records)} records")
                else:
                    results["details"][sheet_name] = {"status": "NO_RECORDS", "records": 0}
                    
            except Exception as e:
                msg = f"{sheet_name}: {str(e)}"
                results["errors"].append(msg)
                logger.error(msg)
                continue
    
    if results["errors"]:
        results["status"] = "PARTIAL"
    return results

MODULE_CONFIG = {
    "BNK": {
        "source_file": "Bnk_TRNX SOURCE.xlsx",
        "sheet_name": "Bnk_Stat_Trnx_Reg",
        "target_table": "bnk_transactions",
        "col_map": {
            "Trnx_Num": "transaction_id",
            "Trnx_Date": "trnx_date",
            "Trnx_Source": "trnx_source",
            "Trnx _Type": "trnx_type",
            "Trnx_Ref": "trnx_ref",
            "Debit": "debit",
            "Credit": "credit",
            "Currency": "currency",
            "Rte_Exc_Average": "rte_exc_average",
            "Narration": "narration",
            "Sub_Led_Code": "sub_led_code",
            "PNR_ID": "pnr_id",
            "Year": "year",
        }
    },
    "SAL": {
        "source_file": "EINV_SAL_TRNX SOURCE.xlsx",
        "sheet_name": "SAL_EINV_REG",
        "target_table": "sales",
        "col_map": {
            "Trnx_Num": "invoice_no",
            "Trnx_Date": "invoice_date",
            "Sub_Led_Mtab_1.Sub_Leg_Code": "client_id",
            "Origi_Trx_Amt": "amount",
            "Currncy": "currency",
            "VAT": "tax_amount",
            "Con_Rate": "conversion_rate",
            "PNR_ID": "cocen_key_id",
        }
    },
    "PUR": {
        "source_file": "EINV_PUR_TRNX SOURCE.xlsx",
        "sheet_name": "PUR_EINV_REG",
        "target_table": "purchase_orders",
        "col_map": {
            "Trnx_Num": "po_no",
            "Trnx_Date": "po_date",
            "Sub_.Sub_Leg_Code": "vendor_id",
            "Total_Inv_Egp_Amt": "amount",
            "Currncy": "currency",
            "VAT": "tax_amount",
            "Con_Rate": "conversion_rate",
            "PNR_ID": "cocen_key_id",
        }
    },
    "EVN": {
        "source_file": "Data_Base_Mtbls.xlsx",
        "sheet_name": "PNR_Mtble",
        "target_table": "events",
        "col_map": {
            "PNR_ID": "pnr_id",
            "CoCen_Key_ID": "cocen_key_id",
            "Client ID": "client_id",
            "Branch ": "branch",
            "Event Name -Description": "event_description",
            "Start Date ": "start_date",
            "End Date": "end_date",
            "Size": "size",
            "Venue": "avenue",
            "Location": "location",
            "Currancy": "currency_id",
            "Total cost": "gross_sales",
        }
    },
    "ENV": {
        "source_file": None,
        "target_table": "environmental",
        "col_map": {},
    },
}
def extract_module_data(module: str, source_file: Optional[str] = None, dry_run: bool = True) -> Dict[str, Any]:
    config = MODULE_CONFIG.get(module)
    if not config:
        return {"status": "ERROR", "error": f"Unknown module: {module}"}
    
    source_filename = source_file or config.get("source_file")
    if not source_filename:
        return {"status": "SKIPPED", "module": module, "error": "No source file configured"}
    
    file_path = resolve_source_file(source_filename)
    target_table = config["target_table"]
    col_map = config.get("col_map", {})
    sheet_name = config.get("sheet_name")
    
    result = {
        "status": "SUCCESS", "module": module, "source_file": file_path,
        "target_table": target_table, "records_read": 0, "records_inserted": 0,
        "errors": [], "dry_run": dry_run,
    }
    
    try:
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)
    except FileNotFoundError:
        result["status"] = "ERROR"
        result["errors"].append(f"File not found: {file_path}")
        return result
    except Exception as e:
        result["status"] = "ERROR"
        result["errors"].append(f"Error reading Excel: {str(e)}")
        return result
    
    if df.empty:
        result["errors"].append("Excel sheet is empty")
        return result
    
    df.rename(columns=col_map, inplace=True)
    
    if module == "BNK":
        df["amount"] = pd.to_numeric(df.get("debit", 0), errors="coerce").fillna(0) -                        pd.to_numeric(df.get("credit", 0), errors="coerce").fillna(0)
        if "check_book_id" not in df.columns:
            df["check_book_id"] = ""
        if "narration" not in df.columns and "Trnx_Ref" in df.columns:
            df["narration"] = df["Trnx_Ref"].astype(str)
        if "currency" not in df.columns:
            df["currency"] = "EGP"
    
    df["_extracted_at"] = datetime.now().isoformat()
    df["_batch_id"] = f"{module.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    df["_module"] = module
    
    result["records_read"] = len(df)
    
    if dry_run:
        result["preview"] = df.head(5).to_dict(orient="records")
        return result
    
    with get_db() as conn:
        try:
            # Get existing columns from the target table
            cursor = conn.execute(f"PRAGMA table_info({target_table})")
            table_cols = [row[1] for row in cursor.fetchall()]
            
            # Only insert columns that exist in both df and the table
            insert_cols = [c for c in df.columns if c in table_cols]
            
            if not insert_cols:
                result["status"] = "ERROR"
                result["errors"].append("No matching columns between source and table")
                return result
            
            placeholders = ", ".join(["?"] * len(insert_cols))
            cols_sql = ", ".join(insert_cols)
            insert_sql = f"INSERT INTO {target_table} ({cols_sql}) VALUES ({placeholders})"
            
            records = []
            for _, row in df.iterrows():
                rec = []
                for col in insert_cols:
                    val = row.get(col)
                    if pd.isna(val):
                        rec.append(None)
                    elif isinstance(val, (int, float)):
                        rec.append(val)
                    else:
                        rec.append(str(val))
                records.append(tuple(rec))
            
            conn.executemany(insert_sql, records)
            conn.commit()
            result["records_inserted"] = len(records)
            logger.info(f"Module: {module} -> {target_table}: {len(records)} records")
            
        except Exception as e:
            result["status"] = "ERROR"
            result["errors"].append(f"Database insert error: {str(e)}")
            logger.error(f"Insert error for {module}: {e}")
    
    return result