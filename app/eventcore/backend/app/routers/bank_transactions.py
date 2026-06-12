import logging
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.bank_transaction import BankTransaction
from app.models.job_line_item import JobLineItem
from app.schemas.bank_transaction import (
    BankTransactionResponse,
    BankTransactionLinkRequest,
)
from app.core.retry import with_retry
from app.core.debounce import debounce

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bank-transactions", tags=["Bank Transactions"])


@router.get("", response_model=list[BankTransactionResponse])
async def list_bank_transactions(
    reconciled: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(BankTransaction).order_by(BankTransaction.transaction_date.desc())
    if reconciled is not None:
        q = q.where(BankTransaction.is_reconciled == reconciled)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/unreconciled", response_model=list[BankTransactionResponse])
async def list_unreconciled(db: AsyncSession = Depends(get_db)):
    q = (
        select(BankTransaction)
        .where(BankTransaction.is_reconciled == False)
        .order_by(BankTransaction.transaction_date.desc())
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/{transaction_id}/link", response_model=BankTransactionResponse)
async def link_bank_transaction(
    transaction_id: UUID,
    payload: BankTransactionLinkRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BankTransaction).where(BankTransaction.id == transaction_id)
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(404, "Bank transaction not found")

    tx.linked_job_id = payload.job_id
    tx.linked_method = payload.linked_method
    tx.is_reconciled = True
    tx.reconciled_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(tx)
    return tx


@router.post("/batch-link")
@debounce("batch-link", cooldown=30.0)
@with_retry(max_retries=3, delay=30.0, backoff=2.0)
async def batch_link_bank_transactions(db: AsyncSession = Depends(get_db)):
    """Auto-link bank transactions to jobs based on description/counterparty matching.
    Matches against: purchase invoice vendors, sales invoice clients, and job event names.
    Retries up to 3 times with exponential backoff. Debounced to prevent cascade calls within 30s.
    """
    import re

    # Fetch unlinked bank transactions
    raw = await db.execute(text("""
        SELECT id, description, counterparty FROM bank_transactions
        WHERE linked_job_id IS NULL AND (description IS NOT NULL OR counterparty IS NOT NULL)
    """))
    rows = raw.all()

    # Fetch purchase invoice vendor names and their job_ids
    raw2 = await db.execute(text("""
        SELECT id, vendor_name, job_id FROM purchase_invoices
    """))
    purchases = [{"id": str(r[0]), "name": str(r[1]).strip().upper(), "job_id": str(r[2]) if r[2] else None} for r in raw2.all()]

    # Fetch sales invoice client names and their job_ids
    raw3 = await db.execute(text("""
        SELECT si.id, c.name, si.job_id
        FROM sales_invoices si
        JOIN clients c ON c.id = si.client_id
    """))
    sales_invs = [{"id": str(r[0]), "name": str(r[1]).strip().upper(), "job_id": str(r[2]) if r[2] else None} for r in raw3.all()]

    # Fetch all jobs with event names
    raw4 = await db.execute(text("""
        SELECT id, event_name FROM jobs
    """))
    jobs = {str(r[0]): str(r[1]).strip().upper() for r in raw4.all()}

    # Fetch all client and vendor names for counterparty matching
    raw5 = await db.execute(text("SELECT name FROM clients"))
    client_names = [str(r[0]).strip().upper() for r in raw5.all()]
    raw6 = await db.execute(text("SELECT vendor_name FROM purchase_invoices"))
    vendor_names = [str(r[0]).strip().upper() for r in raw6.all()]

    SKIP_KEYWORDS = ['MAINTENANCE FEE', 'SERVICE CHARGE', 'STMT CHGS', 'BO CHARGES',
                     'SALARY', 'ALLOWANCE', 'PERSONAL', 'TAX', 'VAT', 'ZAKAT']

    linked = 0

    for tx_id, description, counterparty in rows:
        desc = str(description).upper() if description else ''
        cp = str(counterparty).upper() if counterparty else ''

        # Skip non-business transactions
        if any(k in desc or k in cp for k in SKIP_KEYWORDS):
            continue

        linked_job_id = None
        linked_method = None

        # --- STRATEGY 1: Match description against purchase invoice vendor names ---
        if 'REF NUM' in desc:
            m = re.search(r'REF NUM:O\d+\s+(.+?)\s+\d{6,}', desc)
            if m:
                name = re.sub(r'\s+(MS|MICROSOFT|EVENT|E FINANCE|EFINANCE).*$', '', m.group(1), flags=re.IGNORECASE).strip().upper()
                for p in purchases:
                    if not p['job_id']:
                        continue
                    if name in p['name'] or p['name'] in name:
                        linked_job_id = p['job_id']
                        linked_method = 'auto_ref_purchase'
                        break

        # --- STRATEGY 2: Match counterparty against vendor names ---
        if not linked_job_id and cp:
            for p in purchases:
                if not p['job_id']:
                    continue
                if cp in p['name'] or p['name'] in cp:
                    linked_job_id = p['job_id']
                    linked_method = 'auto_cp_vendor'
                    break

        # --- STRATEGY 3: Match counterparty against sales client names ---
        if not linked_job_id and cp:
            for s in sales_invs:
                if not s['job_id']:
                    continue
                if cp in s['name'] or s['name'] in cp:
                    linked_job_id = s['job_id']
                    linked_method = 'auto_cp_client'
                    break

        # --- STRATEGY 4: Match description against sales client names ---
        if not linked_job_id and desc:
            for s in sales_invs:
                if not s['job_id']:
                    continue
                if s['name'] in desc:
                    linked_job_id = s['job_id']
                    linked_method = 'auto_desc_client'
                    break

        # --- STRATEGY 5: Match description/counterparty against job event names ---
        if not linked_job_id:
            search_text = desc + ' ' + cp
            for jid, event_name in jobs.items():
                if event_name and event_name in search_text:
                    linked_job_id = jid
                    linked_method = 'auto_event_name'
                    break

        # --- STRATEGY 6: Match counterparty against any known name ---
        if not linked_job_id and cp:
            all_names = vendor_names + client_names
            for name in all_names:
                if cp in name or name in cp:
                    linked_method = 'auto_cp_known'
                    break

        # Apply the link if found
        if linked_job_id:
            await db.execute(
                text("""
                    UPDATE bank_transactions
                    SET linked_job_id = :jid,
                        is_reconciled = TRUE,
                        linked_method = :method,
                        match_reason = :reason,
                        reconciled_at = NOW()
                    WHERE id = :tid
                """),
                {"jid": str(linked_job_id), "method": linked_method, "reason": linked_method, "tid": str(tx_id)}
            )
            linked += 1
        elif linked_method == 'auto_cp_known':
            await db.execute(
                text("""
                    UPDATE bank_transactions
                    SET is_reconciled = TRUE,
                        linked_method = :method,
                        match_reason = :reason,
                        reconciled_at = NOW()
                    WHERE id = :tid
                """),
                {"method": linked_method, "reason": linked_method, "tid": str(tx_id)}
            )
            linked += 1

    await db.commit()
    return {"linked": linked, "message": f"Auto-linked {linked} bank transactions"}


@router.post("/batch-link/reset")
async def reset_batch_link_debounce():
    from app.core.debounce import _last_run
    _last_run.pop("batch-link:run", None)
    return {"debounce_reset": True}

