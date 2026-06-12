from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine
from app.models.journal_voucher import JournalVoucher
from app.models.job import Job
from app.models.job_line_item import JobLineItem
from app.models.chart_account import ChartAccount
from app.models.event import Event
from app.schemas.account import (
    JournalVoucherCreate, JournalVoucherResponse,
    TrialBalanceItem, ProfitLossItem,
    ChartAccountCreate, ChartAccountResponse,
)

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])


# Journal Vouchers
@router.post("/journal-vouchers", response_model=JournalVoucherResponse, status_code=201)
async def create_journal_voucher(payload: JournalVoucherCreate, db: AsyncSession = Depends(get_db)):
    jv = JournalVoucher(**payload.model_dump())
    db.add(jv)
    await db.flush()
    await db.refresh(jv)
    return jv


@router.get("/journal-vouchers", response_model=list[JournalVoucherResponse])
async def list_journal_vouchers(
    job_id: UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(JournalVoucher).order_by(JournalVoucher.voucher_date.desc())
    if job_id:
        q = q.where(JournalVoucher.job_id == job_id)
    if status:
        q = q.where(JournalVoucher.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/journal-vouchers/{voucher_id}", response_model=JournalVoucherResponse)
async def get_journal_voucher(voucher_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JournalVoucher).where(JournalVoucher.id == voucher_id))
    jv = result.scalar_one_or_none()
    if not jv:
        raise HTTPException(404, "Journal voucher not found")
    return jv


# Dashboard / Trial Balance
@router.get("/dashboard/stats")
async def get_accounts_dashboard(db: AsyncSession = Depends(get_db)):
    total_revenue = await db.scalar(select(func.coalesce(func.sum(Job.total_revenue), 0))) or 0
    total_cost = await db.scalar(select(func.coalesce(func.sum(Job.total_cost), 0))) or 0
    jv_count = await db.scalar(select(func.count(JournalVoucher.id))) or 0
    return {
        "total_revenue": float(total_revenue),
        "total_cost": float(total_cost),
        "gross_profit": float(total_revenue) - float(total_cost),
        "journal_voucher_count": jv_count,
    }


@router.get("/trial-balance")
async def get_trial_balance(db: AsyncSession = Depends(get_db)):
    revenue = await db.scalar(select(func.coalesce(func.sum(Job.total_revenue), 0))) or 0
    cost = await db.scalar(select(func.coalesce(func.sum(Job.total_cost), 0))) or 0
    return {
        "accounts": [
            {"account_code": "4000", "account_name": "Revenue - Jobs", "debit": 0, "credit": float(revenue), "balance": float(revenue)},
            {"account_code": "5000", "account_name": "Cost - Jobs", "debit": float(cost), "credit": 0, "balance": -float(cost)},
        ],
        "total_debit": float(cost),
        "total_credit": float(revenue),
    }


@router.get("/profit-loss")
async def get_profit_loss(db: AsyncSession = Depends(get_db)):
    categories = ["Accommodation", "Catering", "AV Equipment", "Transport", "Activities", "Management Fees", "Other Items"]

    result = []
    for cat in categories:
        rev = await db.scalar(
            select(func.coalesce(func.sum(JobLineItem.total_amount), 0))
            .where(JobLineItem.type == "revenue", JobLineItem.category == cat, JobLineItem.is_committed == True)
        ) or 0
        cost = await db.scalar(
            select(func.coalesce(func.sum(JobLineItem.total_amount), 0))
            .where(JobLineItem.type == "cost", JobLineItem.category == cat, JobLineItem.is_committed == True)
        ) or 0
        if float(rev) or float(cost):
            result.append({"category": cat, "revenue": float(rev), "cost": float(cost), "gross_profit": float(rev) - float(cost)})

    return result


@router.post("/chart-accounts", response_model=ChartAccountResponse, status_code=201)
async def create_chart_account(payload: ChartAccountCreate, db: AsyncSession = Depends(get_db)):
    acct = ChartAccount(**payload.model_dump())
    db.add(acct)
    await db.flush()
    await db.refresh(acct)
    return acct


@router.get("/chart-accounts", response_model=list[ChartAccountResponse])
async def list_chart_accounts(
    account_type: str | None = Query(None),
    is_cos: bool | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(ChartAccount).order_by(ChartAccount.account_code)
    if account_type:
        q = q.where(ChartAccount.account_type == account_type)
    if is_cos is not None:
        q = q.where(ChartAccount.is_cos == is_cos)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/migrate-cos-accounts")
async def migrate_cos_accounts(db: AsyncSession = Depends(get_db)):
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chart_accounts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                account_code VARCHAR(20) UNIQUE NOT NULL,
                account_name VARCHAR(255) NOT NULL,
                account_type VARCHAR(20) NOT NULL,
                is_cos BOOLEAN DEFAULT FALSE,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'events' AND column_name = 'cos_account_code'
                ) THEN
                    ALTER TABLE events ADD COLUMN cos_account_code VARCHAR(20);
                END IF;
            END $$;
        """))

    defaults = [
        ("5100", "COS - Accommodation", "cost", True),
        ("5200", "COS - Catering", "cost", True),
        ("5300", "COS - AV Equipment", "cost", True),
        ("5400", "COS - Transport", "cost", True),
        ("5500", "COS - Activities", "cost", True),
        ("5600", "COS - Management Fees", "cost", True),
        ("5700", "COS - Other Items", "cost", True),
        ("4000", "Revenue - Events", "revenue", False),
        ("5000", "Cost of Sales", "cost", True),
    ]
    seeded = 0
    for code, name, atype, is_cos in defaults:
        exists = await db.scalar(
            select(ChartAccount).where(ChartAccount.account_code == code)
        )
        if not exists:
            db.add(ChartAccount(account_code=code, account_name=name, account_type=atype, is_cos=is_cos))
            seeded += 1

    cos_map = {
        "conference": "5100",
        "workshop": "5200",
        "gala_dinner": "5500",
        "corporate_event": "5600",
    }
    events_result = await db.execute(
        select(Event).where(Event.cos_account_code.is_(None))
    )
    updated_events = 0
    for ev in events_result.scalars().all():
        code = cos_map.get(ev.event_type)
        if code:
            ev.cos_account_code = code
            updated_events += 1
    await db.flush()
    return {
        "table_created": True,
        "accounts_seeded": seeded,
        "events_updated": updated_events,
        "total_accounts": len(defaults),
    }
