"""Phase 1v3: Migrate production data from SQLite eventcore.db to PostgreSQL.
Uses a new connection per table to avoid transaction state issues.
Pre-filters orphaned FK references."""

import sqlite3
import uuid
import asyncio
import logging
from datetime import datetime, date

from sqlalchemy import text, create_engine
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate")

SQLITE_PATH = r"D:\eventmanager-erp\backend\eventcore.db"

TABLE_ORDER = [
    "users", "company_profiles", "categories", "sub_categories",
    "clients", "vendors", "employees", "jobs", "events",
    "cost_centers", "quotations", "quotation_line_items",
    "purchase_invoices", "sales_invoices", "sales_invoice_line_items",
    "bank_transactions", "payment_vouchers", "petty_cash",
    "journal_vouchers", "vat_returns", "leave_requests",
    "task_assignments", "activity_log", "job_line_items",
]

SQLITE_ONLY_COLUMNS = {"categories": {"module_origin"}, "job_line_items": {"item_number"}}
PG_ONLY_DEFAULTS = {"events": {"cos_account_code": "5700"}, "purchase_invoices": {"event_id": None}}
SKIP_TABLES = {"purchase_categories", "purchase_sub_categories"}

UUID_COLUMNS = {
    "id", "job_id", "client_id", "vendor_id", "user_id", "employee_id",
    "linked_job_id", "event_id", "purchase_invoice_id", "sales_invoice_id",
    "invoice_id", "quotation_id", "budget_line_id", "converted_to_job_id",
    "cost_center_id", "payment_voucher_id", "import_batch_id",
    "source_id", "linked_by", "created_by", "approved_by", "reconciled_by",
    "posted_by", "submitted_by",
}

DATETIME_COLUMNS = {
    "created_at", "updated_at", "reconciled_at", "linked_at", "imported_at",
    "submitted_at", "posted_at", "reimbursed_at", "approved_at",
    "invoice_date", "due_date", "transaction_date", "start_date", "end_date",
    "quote_date", "valid_until", "hire_date", "expense_date", "payment_date",
    "voucher_date", "event_dates", "period_start", "period_end",
    "leave_start_date", "leave_end_date",
}

DATE_ONLY_COLUMNS = {
    "transaction_date", "invoice_date", "due_date", "start_date", "end_date",
    "quote_date", "valid_until", "hire_date", "expense_date", "payment_date",
    "voucher_date", "period_start", "period_end", "leave_start_date", "leave_end_date",
    "event_dates",
}

BOOL_COLUMNS = {
    "is_reconciled", "is_active", "is_committed", "is_locked", "is_closed",
    "is_synced", "has_receipt", "is_cos",
}


def get_sqlite_columns(cursor, table_name):
    cursor.execute(f'PRAGMA table_info("{table_name}")')
    return {r[1]: r[2] for r in cursor.fetchall()}


def coerce(value, col_name, sqlite_type):
    if value is None:
        return None
    if col_name in UUID_COLUMNS:
        s = str(value).strip()
        try:
            return str(uuid.UUID(s))
        except ValueError:
            return s
    if col_name in DATE_ONLY_COLUMNS and isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return value[:10] if len(value) >= 10 else value
    if col_name in DATETIME_COLUMNS and isinstance(value, str):
        try:
            return value.replace("T", " ").split(".")[0][:19]
        except Exception:
            return value
    if col_name in BOOL_COLUMNS:
        if isinstance(value, int):
            return bool(value)
        return value
    if sqlite_type == "INTEGER" and not isinstance(value, int):
        try:
            return int(value)
        except (ValueError, TypeError):
            return value
    return value


async def main():
    if "sqlite" in settings.database_url:
        logger.error(f"DATABASE_URL is SQLite: {settings.database_url}")
        return

    logger.info(f"Source: SQLite @ {SQLITE_PATH}")
    logger.info(f"Target: PostgreSQL @ {settings.database_url}")

    sl_conn = sqlite3.connect(SQLITE_PATH)
    sl_conn.row_factory = sqlite3.Row
    sl = sl_conn.cursor()

    # Create a sync PG engine for the truncate
    # Use synchronous psycopg2 for simplicity here
    pg_url = settings.database_url.replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2", "postgresql")
    sync_engine = create_engine(pg_url)

    with sync_engine.begin() as pg_sync:
        pg_sync.execute(text("""
            TRUNCATE TABLE events, jobs, clients, vendors, bank_transactions,
            purchase_invoices, sales_invoices, payment_vouchers, quotations,
            quotation_line_items, sales_invoice_line_items, job_line_items,
            journal_vouchers, petty_cash, activity_log, cost_centers, employees,
            leave_requests, task_assignments, vat_returns, budget_commitments,
            budget_lines, budget_periods, e_invoice_lines, company_profiles,
            categories, sub_categories, users CASCADE
        """))
        logger.info("All tables truncated")

    # Pre-collect SQLite column info for all tables
    sqlite_cols_map = {}
    sl.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for r in sl.fetchall():
        sqlite_cols_map[r[0]] = get_sqlite_columns(sl, r[0])

    total_rows = 0
    for table_name in TABLE_ORDER:
        if table_name not in sqlite_cols_map:
            logger.info(f"  {table_name}: not in SQLite, skipping")
            continue

        sqlite_cols = sqlite_cols_map[table_name]
        skip = SQLITE_ONLY_COLUMNS.get(table_name, set())

        # Get PG columns via sync engine
        with sync_engine.connect() as pg_sync:
            result = pg_sync.execute(
                text("SELECT column_name FROM information_schema.columns "
                     "WHERE table_schema='public' AND table_name=:t ORDER BY ordinal_position"),
                {"t": table_name}
            )
            pg_cols_set = {r[0] for r in result.fetchall()}

        common = [c for c in sqlite_cols if c in pg_cols_set and c not in skip]
        if not common:
            logger.info(f"  {table_name}: no common columns, skipping")
            continue

        col_list = ", ".join(f'"{c}"' for c in common)
        sl.execute(f'SELECT {col_list} FROM "{table_name}"')
        rows = sl.fetchall()
        if not rows:
            logger.info(f"  {table_name}: 0 rows, skipping")
            continue

        # For job_line_items, pre-filter by valid job IDs
        if table_name == "job_line_items":
            with sync_engine.connect() as pg_sync:
                valid_jobs = {r[0] for r in pg_sync.execute(text("SELECT id FROM jobs")).fetchall()}
            before = len(rows)
            rows = [r for r in rows if r["job_id"] in valid_jobs]
            logger.info(f"  {table_name}: {before} total, {len(rows)} after filtering orphaned job_ids")
            if not rows:
                continue

        # Fix corrupted column data
        if table_name == "events":
            fixed_rows = []
            for row in rows:
                d = dict(row)
                sd = str(d.get("start_date", "") or "")
                ed = str(d.get("end_date", "") or "")
                # If start_date is not a valid date, use end_date
                if sd and not sd[0:4].isdigit():
                    d["start_date"] = ed if ed else "2024-01-01"
                # If end_date is not a valid date, use start_date
                if ed and not ed[0:4].isdigit():
                    d["end_date"] = sd if sd else "2024-01-01"
                fixed_rows.append(d)
            rows = fixed_rows

        defaults = PG_ONLY_DEFAULTS.get(table_name, {})
        insert_cols = list(common)
        for col in defaults:
            if col not in insert_cols:
                insert_cols.append(col)
        pg_col_list = ", ".join(f'"{c}"' for c in insert_cols)
        param_list = ", ".join(f":{c}" for c in insert_cols)
        insert_sql = f'INSERT INTO "{table_name}" ({pg_col_list}) VALUES ({param_list})'

        success = 0
        errors = 0
        batch_size = 100

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            params_batch = []
            for row in batch:
                params = {}
                for col in common:
                    params[col] = coerce(row[col], col, sqlite_cols.get(col, "TEXT"))
                for col, val in defaults.items():
                    params[col] = val
                params_batch.append(params)

            with sync_engine.begin() as pg_sync:
                try:
                    pg_sync.execute(text(insert_sql), params_batch)
                    success += len(batch)
                except Exception as e:
                    logger.warning(f"    Batch failed for {table_name} at row {i}: {e}")
                    # Row-by-row in a fresh transaction
                    for p in params_batch:
                        try:
                            with sync_engine.begin() as pg_sub:
                                pg_sub.execute(text(insert_sql), p)
                            success += 1
                        except Exception as e2:
                            errors += 1
                            if errors <= 5:
                                logger.warning(f"    Skipping row in {table_name}: {e2}")

        total_rows += success
        if errors:
            logger.info(f"  {table_name}: {success} inserted, {errors} skipped")
        else:
            logger.info(f"  {table_name}: {success} rows migrated")

    logger.info(f"\n✅ Total: {total_rows} rows migrated to PostgreSQL")
    sl_conn.close()


if __name__ == "__main__":
    asyncio.run(main())
