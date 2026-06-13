"""
load_rich_data.py — Phase 5 Data Injection (corrected for actual Excel structure)
Injects Excel source data into empty DB tables with full audit trail.

Reality: Sales Ladger has merged-cell 3-value arrays per column → skip SalesInvoiceLine
Targets: ServiceMainCategory, ServiceSubCategory, PNRBudgetLineItem

Usage:
  python -m app.inject.load_rich_data --dry-run
  python -m app.inject.load_rich_data
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
BACKUP_DIR = Path(__file__).resolve().parent.parent.parent / "STAGING_BRIDGE"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "production"

LOG_DIR.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"data_injection_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("DataInjection")

EXCEL_FILE = DATA_DIR / "Incentive House Fullmodules.xlsx"

# Known service categories from Sales Ladger column headers (col 12-23)
# DB schema: ServiceMainCategory(MainCategoryCode PK, MainCategoryName, DisplayOrder)
#            ServiceSubCategory(SubCategoryCode PK, MainCategoryCode FK, SubCategoryName, DefaultVendorCode, GLAccount)
SERVICE_CATEGORIES = [
    ("ACC", "Accommodation"),
    ("ATV", "Air Ticketing & Visa"),
    ("TRN", "Transfers & Transportation"),
    ("FNB", "Food & Beverage"),
    ("RNT", "Rent"),
    ("PNS", "Printing & Stationary"),
    ("VAT", "VAT"),
    ("MTP", "Meeting Package"),
    ("BRN", "Branding"),
    ("EXT", "Extra Event Supports"),
    ("MGT", "Management Fees"),
]

KNOWN_CATEGORIES = {
    "SALES": ("Sales", SERVICE_CATEGORIES),
    "COST":  ("Cost",  SERVICE_CATEGORIES),
}

# PNRBudgetLineItem columns: LineItemID, Year, JobFolder, FileName, SheetName, RowNumber,
#   MainCategoryCode, SubCategoryCode, ClientCode, Description, Quantity, UnitPrice, Amount,
#   CurrencyCode, C1-C20, IsHeaderRow


def get_session():
    from app.database import SyncSessionLocal
    return SyncSessionLocal()


# ── Injection Functions ──────────────────────────────────────────────────────

def inject_service_categories(session, dry_run: bool) -> Dict:
    """Create known service categories from Sales Ladger column structure."""
    results = {}

    if dry_run:
        n_sub = sum(len(subs) for _, subs in KNOWN_CATEGORIES.values())
        logger.info(f"  [DRY-RUN] Would create: {len(KNOWN_CATEGORIES)} main + {n_sub} sub categories")
        return {
            "ServiceMainCategory": {"status": "VALIDATED", "rows": len(KNOWN_CATEGORIES)},
            "ServiceSubCategory": {"status": "VALIDATED", "rows": n_sub},
        }

    existing_main = set(
        row[0] for row in session.execute(text("SELECT MainCategoryCode FROM ServiceMainCategory")).fetchall()
    )
    existing_sub = set(
        row[0] for row in session.execute(text("SELECT SubCategoryCode FROM ServiceSubCategory")).fetchall()
    )

    main_count = 0
    sub_count = 0

    for code, (name, sub_list) in KNOWN_CATEGORIES.items():
        if code not in existing_main:
            session.execute(
                text("INSERT INTO ServiceMainCategory (MainCategoryCode, MainCategoryName, DisplayOrder) VALUES (:c, :n, :o)"),
                {"c": code, "n": name, "o": len(existing_main) + main_count + 1},
            )
            main_count += 1

        for sc_code, sc_name in sub_list:
            full_sc_code = f"{code}_{sc_code}"
            if full_sc_code not in existing_sub:
                session.execute(
                    text("INSERT INTO ServiceSubCategory (SubCategoryCode, MainCategoryCode, SubCategoryName) VALUES (:sc, :mc, :sn)"),
                    {"sc": full_sc_code, "mc": code, "sn": sc_name},
                )
                sub_count += 1

    logger.info(f"  Created {main_count} new ServiceMainCategory + {sub_count} new ServiceSubCategory entries")
    results["ServiceMainCategory"] = {"status": "INJECTED", "rows": main_count}
    results["ServiceSubCategory"] = {"status": "INJECTED", "rows": sub_count}
    return results


def inject_pnr_budget(session, dry_run: bool) -> Dict:
    """Inject PNR Details rows into PNRBudgetLineItem."""
    df = pd.read_excel(EXCEL_FILE, sheet_name="PNR Details", header=None)
    # Row 0 = empty, Row 1 = header, Row 2+ = data
    if len(df) < 3:
        logger.warning("  PNR Details has insufficient rows")
        return {"PNRBudgetLineItem": {"status": "SKIP", "reason": "Insufficient data"}}

    # Extract data rows (skip row 0 empty, row 1 header)
    data = df.iloc[2:].copy().reset_index(drop=True)
    data = data.dropna(how="all").reset_index(drop=True)

    logger.info(f"  PNR detail rows: {len(data)}")

    # Column indices: 1=PNR-Number, 7=Item Narration, 9=Units/PAX, 10=nights, 11=Unit Price, 12=Value
    if dry_run:
        valid_rows = sum(1 for _, r in data.iterrows() if len(r) > 12 and pd.notna(pd.to_numeric(r.iloc[12], errors="coerce")) and pd.to_numeric(r.iloc[12], errors="coerce") > 0)
        logger.info(f"  [DRY-RUN] Would process ~{valid_rows} rows with Value > 0 into PNRBudgetLineItem")
        return {"PNRBudgetLineItem": {"status": "VALIDATED", "rows": len(data)}}

    inserted = 0
    for idx, row in data.iterrows():
        val = pd.to_numeric(row.iloc[12], errors="coerce") if len(row) > 12 else 0
        if pd.isna(val) or val <= 0:
            continue

        pnr_ref = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        desc = str(row.iloc[7]).strip() if len(row) > 7 and pd.notna(row.iloc[7]) else ""
        qty = pd.to_numeric(row.iloc[9], errors="coerce") if len(row) > 9 else 0
        unit_price = pd.to_numeric(row.iloc[11], errors="coerce") if len(row) > 11 else 0
        client_name = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ""

        session.execute(
            text("""
                INSERT INTO PNRBudgetLineItem
                    (Year, JobFolder, FileName, SheetName, RowNumber,
                     ClientCode, Description, Quantity, UnitPrice, Amount,
                     C1, C2, IsHeaderRow)
                VALUES (:yr, :jf, :fn, :sn, :rn,
                        :cc, :desc, :qty, :up, :amt,
                        :c1, :c2, :hdr)
            """),
            {
                "yr": 2022,
                "jf": pnr_ref,
                "fn": "Incentive House Fullmodules.xlsx",
                "sn": "PNR Details",
                "rn": int(idx + 3),
                "cc": client_name[:10],
                "desc": desc[:500] if desc else f"PNR Detail row {idx + 3}",
                "qty": float(qty) if pd.notna(qty) and qty > 0 else 1.0,
                "up": float(unit_price) if pd.notna(unit_price) and unit_price > 0 else float(val),
                "amt": float(val),
                "c1": f"PNR: {pnr_ref}" if pnr_ref else "",
                "c2": f"Row: {idx + 3}",
                "hdr": False,
            },
        )
        inserted += 1

    logger.info(f"  Inserted {inserted} rows into PNRBudgetLineItem")
    return {"PNRBudgetLineItem": {"status": "INJECTED", "rows": inserted}}


def verify_tables(session):
    """Log current row counts for all target tables."""
    logger.info(f"\n{'=' * 55}")
    logger.info("  POST-INJECTION TABLE STATE")
    logger.info(f"{'=' * 55}")
    targets = [
        "ServiceMainCategory", "ServiceSubCategory",
        "SalesInvoiceLine", "PNRBudgetLineItem", "PurchaseVoucherLine",
        "SalesInvoice", "PNRMaster", "PurchaseVoucher",
    ]
    for t in targets:
        try:
            cnt = session.execute(text(f"SELECT COUNT(*) FROM dbo.[{t}]")).scalar()
            logger.info(f"  {t:30s}: {cnt:>5} rows")
        except Exception as e:
            logger.info(f"  {t:30s}: ERROR ({e})")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Inject Excel data into IH-ERP DB")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing")
    parser.add_argument("--clear", action="store_true", help="Truncate target tables before insert")
    args = parser.parse_args()

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    logger.info(f"{'=' * 55}")
    logger.info(f"  Phase 5 Data Injection — Mode: {mode}")
    logger.info(f"{'=' * 55}")

    if not EXCEL_FILE.exists():
        logger.error(f"Excel not found: {EXCEL_FILE}")
        sys.exit(1)

    session = get_session()

    if args.clear and not args.dry_run:
        for t in ["ServiceMainCategory", "ServiceSubCategory", "PNRBudgetLineItem"]:
            session.execute(text(f"DELETE FROM dbo.[{t}]"))
            logger.info(f"  Cleared {t}")

    all_results = {}
    try:
        all_results.update(inject_service_categories(session, args.dry_run))
        all_results.update(inject_pnr_budget(session, args.dry_run))

        if args.dry_run:
            session.rollback()
            logger.info(f"\n  DRY-RUN complete — no changes committed")
        else:
            session.commit()
            logger.info(f"\n  LIVE injection committed")

        verify_tables(session)

        # Summary
        logger.info(f"\n{'=' * 55}")
        logger.info("  INJECTION SUMMARY")
        logger.info(f"{'=' * 55}")
        for table, res in all_results.items():
            icon = "OK" if res.get("status") in ("INJECTED", "VALIDATED") else "--"
            logger.info(f"  [{icon}] {table:30s} | {res.get('status','?'):12s} | rows={res.get('rows',0)}")
        logger.info(f"{'=' * 55}")

        BACKUP_DIR.mkdir(exist_ok=True)
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": args.dry_run,
            "results": all_results,
            "log_file": str(log_file),
        }
        manifest_path = BACKUP_DIR / f"injection_manifest_{timestamp}.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, default=str)
        logger.info(f"  Manifest: {manifest_path}")

    except Exception as e:
        session.rollback()
        logger.error(f"FATAL — rolled back: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
