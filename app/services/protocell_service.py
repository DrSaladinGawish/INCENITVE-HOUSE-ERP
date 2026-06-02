import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import (
    COAMaster, PNRDim, VendorDim, ClientDim, CurrencyRate,
    BnkStaging, SalesStaging, PurchaseStaging, EventsStaging, EnvironmentalStaging,
)


async def validate_rule_mandatory_fields(rows: List[Dict]) -> Dict:
    passed = 0; warnings = 0; errors = 0; details = []
    for i, row in enumerate(rows):
        issues = []
        if not row.get("transaction_id"): issues.append("Missing transaction_id")
        if not row.get("transaction_date"): issues.append("Missing transaction_date")
        if not row.get("amount") and row.get("debit", 0) == 0 and row.get("credit", 0) == 0:
            issues.append("Zero amount")
        if not row.get("description") and not row.get("narration"):
            issues.append("Missing description/narration")
        if not row.get("_module"): issues.append("Missing module_source")
        if issues:
            errors += 1
            details.append({"row": i, "issues": issues, "severity": "ERROR"})
        else:
            passed += 1
    return {"rule": "Mandatory Fields", "passed": errors == 0, "passed_count": passed, "warning_count": warnings, "error_count": errors, "details": details}


async def validate_rule_sub_led_code(rows: List[Dict], db: AsyncSession) -> Dict:
    result = await db.execute(select(COAMaster.acc_key).where(COAMaster.is_active == True))
    valid_codes = {row[0] for row in result.all()}
    passed = 0; warnings = 0; errors = 0; details = []
    for i, row in enumerate(rows):
        code = str(row.get("sub_led_code", "")).strip()
        if not code or code == "-":
            warnings += 1; details.append({"row": i, "issues": ["Missing Sub_Led_Code"], "severity": "WARNING"})
        elif code not in valid_codes and valid_codes:
            warnings += 1; details.append({"row": i, "issues": [f"Code {code} not in COA"], "severity": "WARNING"})
        else:
            passed += 1
    return {"rule": "Sub_Led_Code in COA", "passed": errors == 0, "passed_count": passed, "warning_count": warnings, "error_count": errors, "details": details}


async def validate_rule_pnr_id(rows: List[Dict], db: AsyncSession) -> Dict:
    result = await db.execute(select(PNRDim.pnr_code, PNRDim.status).where(PNRDim.status == "active"))
    valid_pnrs = {str(row[0]) for row in result.all()}
    passed = 0; warnings = 0; errors = 0; details = []
    for i, row in enumerate(rows):
        pnr = str(row.get("pnr_id", "")).strip()
        if not pnr or pnr == "-":
            warnings += 1; details.append({"row": i, "issues": ["Missing PNR_ID"], "severity": "WARNING"})
        elif pnr not in valid_pnrs and valid_pnrs:
            warnings += 1; details.append({"row": i, "issues": [f"PNR {pnr} not active"], "severity": "WARNING"})
        else:
            passed += 1
    return {"rule": "PNR_ID in PNR Master", "passed": errors == 0, "passed_count": passed, "warning_count": warnings, "error_count": errors, "details": details}


async def validate_rule_dual_entry(rows: List[Dict]) -> Dict:
    passed = 0; warnings = 0; errors = 0; details = []
    for i, row in enumerate(rows):
        debit = float(row.get("debit", 0) or 0)
        credit = float(row.get("credit", 0) or 0)
        if abs(debit + credit) > 0.01:
            warnings += 1; details.append({"row": i, "issues": [f"Imbalance: debit={debit}, credit={credit}"], "severity": "WARNING"})
        else:
            passed += 1
    return {"rule": "Dual-Entry Balance", "passed": errors == 0, "passed_count": passed, "warning_count": warnings, "error_count": errors, "details": details}


async def validate_rule_date_range(rows: List[Dict]) -> Dict:
    passed = 0; warnings = 0; errors = 0; details = []
    today = datetime.date.today()
    for i, row in enumerate(rows):
        d_str = row.get("transaction_date") or row.get("trnx_date") or row.get("invoice_date")
        if not d_str:
            warnings += 1; details.append({"row": i, "issues": ["No date"], "severity": "WARNING"})
            continue
        try:
            d = datetime.datetime.strptime(str(d_str)[:10], "%Y-%m-%d").date()
            if d > today:
                errors += 1; details.append({"row": i, "issues": ["Future date"], "severity": "ERROR"})
            elif d < datetime.date(2020, 1, 1):
                warnings += 1; details.append({"row": i, "issues": ["Date before 2020"], "severity": "WARNING"})
            else:
                passed += 1
        except ValueError:
            warnings += 1; details.append({"row": i, "issues": [f"Invalid date: {d_str}"], "severity": "WARNING"})
    return {"rule": "Date Validation", "passed": errors == 0, "passed_count": passed, "warning_count": warnings, "error_count": errors, "details": details}


async def validate_rule_amount(rows: List[Dict]) -> Dict:
    passed = 0; warnings = 0; errors = 0; details = []
    for i, row in enumerate(rows):
        amt = abs(float(row.get("amount", 0) or 0))
        debit = float(row.get("debit", 0) or 0)
        credit = float(row.get("credit", 0) or 0)
        max_amt = max(amt, debit, credit)
        if max_amt == 0:
            errors += 1; details.append({"row": i, "issues": ["Zero amount"], "severity": "ERROR"})
        elif max_amt > 10_000_000:
            warnings += 1; details.append({"row": i, "issues": [f"Amount > 10M: {max_amt}"], "severity": "WARNING"})
        elif max_amt != round(max_amt, 2):
            warnings += 1; details.append({"row": i, "issues": ["More than 2 decimal places"], "severity": "WARNING"})
        else:
            passed += 1
    return {"rule": "Amount Validation", "passed": errors == 0, "passed_count": passed, "warning_count": warnings, "error_count": errors, "details": details}


async def validate_rule_duplicates(rows: List[Dict]) -> Dict:
    passed = 0; warnings = 0; errors = 0; details = []
    seen = {}
    for i, row in enumerate(rows):
        tid = row.get("transaction_id") or row.get("invoice_no") or row.get("po_no")
        mod = row.get("_module", "")
        key = f"{tid}|{mod}"
        if tid and key in seen:
            warnings += 1; details.append({"row": i, "issues": [f"Duplicate: {key}"], "severity": "WARNING"})
        else:
            passed += 1
            if tid: seen[key] = i
    return {"rule": "Duplicate Detection", "passed": errors == 0, "passed_count": passed, "warning_count": warnings, "error_count": errors, "details": details}


async def run_all_validations(rows: List[Dict], db: AsyncSession) -> List[Dict]:
    rules = [
        await validate_rule_mandatory_fields(rows),
        await validate_rule_sub_led_code(rows, db),
        await validate_rule_pnr_id(rows, db),
        await validate_rule_dual_entry(rows),
        await validate_rule_date_range(rows),
        await validate_rule_amount(rows),
        await validate_rule_duplicates(rows),
    ]
    return rules


def rows_from_staging(module: str, staging_rows) -> List[Dict]:
    rows = []
    for r in staging_rows:
        d = dict(r._mapping)
        d["_module"] = module
        if not d.get("description"):
            d["description"] = d.get("narration", "")
        rows.append(d)
    return rows


def generate_journal_entries(staging_rows: List[Dict], source: str, coa_map: Dict) -> List[Dict]:
    entries = []
    for row in staging_rows:
        d = dict(row._mapping) if hasattr(row, "_mapping") else row
        debit = float(d.get("debit", 0) or 0)
        credit = float(d.get("credit", 0) or 0)
        amt = abs(debit) if debit else abs(credit)
        pnr = str(d.get("pnr_id", "")).strip() or "UNALLOCATED"
        sub_led = str(d.get("sub_led_code", "")).strip()
        date_val = d.get("transaction_date") or d.get("trnx_date") or d.get("invoice_date")
        name = d.get("narration") or d.get("description") or ""
        if debit > 0:
            entries.append({"source": source, "trnx_num": str(d.get("transaction_id", "")), "trnx_date": str(date_val)[:10] if date_val else "", "account_id": "4", "acc_name": "Cash at Bank", "debit": round(amt, 2), "credit": 0, "sub_led_code": sub_led, "pnr_id": pnr, "narration": name, "status": "VALID", "currency": str(d.get("currency", "EGP"))})
            entries.append({"source": source, "trnx_num": str(d.get("transaction_id", "")), "trnx_date": str(date_val)[:10] if date_val else "", "account_id": "12", "acc_name": coa_map.get(sub_led, "Accounts Payables"), "debit": 0, "credit": round(amt, 2), "sub_led_code": sub_led, "pnr_id": pnr, "narration": name, "status": "VALID", "currency": str(d.get("currency", "EGP"))})
        elif credit > 0:
            entries.append({"source": source, "trnx_num": str(d.get("transaction_id", "")), "trnx_date": str(date_val)[:10] if date_val else "", "account_id": "12", "acc_name": coa_map.get(sub_led, "Accounts Payables"), "debit": round(amt, 2), "credit": 0, "sub_led_code": sub_led, "pnr_id": pnr, "narration": name, "status": "VALID", "currency": str(d.get("currency", "EGP"))})
            entries.append({"source": source, "trnx_num": str(d.get("transaction_id", "")), "trnx_date": str(date_val)[:10] if date_val else "", "account_id": "4", "acc_name": "Cash at Bank", "debit": 0, "credit": round(amt, 2), "sub_led_code": sub_led, "pnr_id": pnr, "narration": name, "status": "VALID", "currency": str(d.get("currency", "EGP"))})
    return entries


def verify_balanced(entries: List[Dict]) -> Dict:
    total_debit = round(sum(e["debit"] for e in entries), 2)
    total_credit = round(sum(e["credit"] for e in entries), 2)
    diff = round(total_debit - total_credit, 2)
    return {"total_debit": total_debit, "total_credit": total_credit, "difference": diff, "balanced": abs(diff) < 0.01, "entry_count": len(entries)}
