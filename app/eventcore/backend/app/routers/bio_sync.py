"""Bulk Bio-ERP sync — pushes clean EventCore data to port 8000."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from app.database import get_db
from app.config import settings
from app.core.surgery_deps import get_current_user

router = APIRouter(prefix="/api/v1/bio-sync", tags=["Bio-ERP Sync"])


async def _post_to_bio(endpoint: str, payload: list) -> dict:
    url = f"{settings.bio_erp_base_url.rstrip('/')}{endpoint}"
    headers = {
        "X-Bridge-Token": settings.bio_erp_api_key,
        "Content-Type": "application/json",
        "X-Correlation-ID": str(datetime.now(timezone.utc).timestamp()),
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


@router.post("/push-all")
async def push_all_to_bio(db: AsyncSession = Depends(get_db)):
    """Push all clean EventCore data to Bio-ERP in one batch."""
    batch_id = f"EC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    results = []

    # Health check
    bio_online = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.bio_erp_base_url.rstrip('/')}/health")
            bio_online = r.status_code == 200
    except Exception:
        bio_online = False

    if not bio_online:
        raise HTTPException(503, "Bio-ERP is offline at " + settings.bio_erp_base_url)

    # 1. Vendors (active only)
    try:
        rows = (await db.execute(text("SELECT id, name, category, contact_person, email, phone, vat_number, bank_account, bank_name, currency, payment_terms, status FROM vendors WHERE status = 'active'"))).mappings().all()
        payload = [dict(r) for r in rows]
        if payload:
            resp = await _post_to_bio("/api/v1/or/eventcore/vendors", payload)
            results.append({"entity": "vendors", "sent": len(payload), "accepted": resp.get("accepted", 0), "rejected": resp.get("rejected", 0), "errors": resp.get("errors", [])})
        else:
            results.append({"entity": "vendors", "sent": 0, "accepted": 0, "rejected": 0, "errors": []})
    except Exception as e:
        results.append({"entity": "vendors", "sent": 0, "accepted": 0, "rejected": 0, "errors": [str(e)]})

    # 2. Chart accounts (active)
    try:
        rows = (await db.execute(text("SELECT id, account_code, account_name, account_type, is_cos, description, is_active FROM chart_accounts WHERE is_active = 1"))).mappings().all()
        payload = [dict(r) for r in rows]
        if payload:
            resp = await _post_to_bio("/api/v1/or/eventcore/gl-accounts", payload)
            results.append({"entity": "gl_accounts", "sent": len(payload), "accepted": resp.get("accepted", 0), "rejected": resp.get("rejected", 0), "errors": resp.get("errors", [])})
        else:
            results.append({"entity": "gl_accounts", "sent": 0, "accepted": 0, "rejected": 0, "errors": []})
    except Exception as e:
        results.append({"entity": "gl_accounts", "sent": 0, "accepted": 0, "rejected": 0, "errors": [str(e)]})

    # 3. Journal vouchers (clean only: amount > 0)
    try:
        rows = (await db.execute(text("SELECT id, voucher_number, voucher_date, job_id, description, debit_account, credit_account, amount, currency, status FROM journal_vouchers WHERE amount IS NOT NULL AND amount > 0"))).mappings().all()
        payload = [dict(r) for r in rows]
        if payload:
            resp = await _post_to_bio("/api/v1/or/eventcore/journal-entries", payload)
            results.append({"entity": "journal_vouchers", "sent": len(payload), "accepted": resp.get("accepted", 0), "rejected": resp.get("rejected", 0), "errors": resp.get("errors", [])})
        else:
            results.append({"entity": "journal_vouchers", "sent": 0, "accepted": 0, "rejected": 0, "errors": []})
    except Exception as e:
        results.append({"entity": "journal_vouchers", "sent": 0, "accepted": 0, "rejected": 0, "errors": [str(e)]})

    # 4. Sales invoices (repaired, amount present)
    try:
        rows = (await db.execute(text("""
            SELECT si.id, si.invoice_number, si.invoice_date, si.due_date, si.job_id, si.client_id, si.total_amount, si.vat_amount, si.subtotal, si.status, c.name as client_name
            FROM sales_invoices si LEFT JOIN clients c ON si.client_id = c.id
            WHERE si.total_amount IS NOT NULL AND si.total_amount > 0
        """))).mappings().all()
        payload = [dict(r) for r in rows]
        if payload:
            resp = await _post_to_bio("/api/v1/or/eventcore/invoices", payload)
            results.append({"entity": "sales_invoices", "sent": len(payload), "accepted": resp.get("accepted", 0), "rejected": resp.get("rejected", 0), "errors": resp.get("errors", [])})
        else:
            results.append({"entity": "sales_invoices", "sent": 0, "accepted": 0, "rejected": 0, "errors": []})
    except Exception as e:
        results.append({"entity": "sales_invoices", "sent": 0, "accepted": 0, "rejected": 0, "errors": [str(e)]})

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "batch_id": batch_id,
        "results": results,
        "bio_erp_online": bio_online,
    }


@router.get("/exclusions")
async def get_exclusions(db: AsyncSession = Depends(get_db)):
    """Report rows permanently excluded from sync."""
    bank = (await db.execute(text("SELECT COUNT(*) as cnt FROM bank_transactions WHERE amount = 0 OR amount IS NULL"))).mappings().first()
    purchase = (await db.execute(text("SELECT COUNT(*) as cnt FROM purchase_invoices WHERE total_amount IS NULL OR total_amount = 0"))).mappings().first()

    return {
        "permanent_gaps": [
            {
                "table": "bank_transactions",
                "excluded_rows": bank["cnt"] if bank else 0,
                "reason": "CSV import stripped monetary values — permanently unrecoverable",
                "recovery_possible": False,
            },
            {
                "table": "purchase_invoices",
                "excluded_rows": purchase["cnt"] if purchase else 0,
                "reason": "No child line_items exist to backfill amounts",
                "recovery_possible": True,
            },
        ],
        "sync_ready_rows": {
            "vendors": (await db.scalar(text("SELECT COUNT(*) FROM vendors WHERE status = 'active'"))) or 0,
            "gl_accounts": (await db.scalar(text("SELECT COUNT(*) FROM chart_accounts WHERE is_active = 1"))) or 0,
            "journal_vouchers": (await db.scalar(text("SELECT COUNT(*) FROM journal_vouchers WHERE amount > 0"))) or 0,
            "sales_invoices": (await db.scalar(text("SELECT COUNT(*) FROM sales_invoices WHERE total_amount > 0"))) or 0,
        },
    }
