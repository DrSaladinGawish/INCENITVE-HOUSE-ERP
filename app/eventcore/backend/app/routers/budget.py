from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine
from app.models.budget_line import BudgetLine
from app.models.budget_period import BudgetPeriod
from app.models.budget_commitment import BudgetCommitment
from app.models.purchase_invoice import PurchaseInvoice
from app.schemas.budget import (
    BudgetLineCreate, BudgetLineResponse,
    BudgetPeriodCreate, BudgetPeriodResponse,
    BudgetCommitmentCreate, BudgetCommitmentResponse,
)


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

router = APIRouter(prefix="/api/v1/budget", tags=["Budget"])


@router.post("/periods", response_model=BudgetPeriodResponse, status_code=201)
async def create_budget_period(
    payload: BudgetPeriodCreate,
    db: AsyncSession = Depends(get_db),
):
    period = BudgetPeriod(
        fiscal_year=payload.fiscal_year,
        quarter=payload.quarter,
        month=payload.month,
        label=payload.label,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(period)
    await db.flush()
    await db.refresh(period)
    return period


@router.get("/periods", response_model=list[BudgetPeriodResponse])
async def list_budget_periods(
    fiscal_year: int | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(BudgetPeriod).order_by(BudgetPeriod.fiscal_year.desc(), BudgetPeriod.label)
    if fiscal_year:
        q = q.where(BudgetPeriod.fiscal_year == fiscal_year)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/lines", response_model=BudgetLineResponse, status_code=201)
async def create_budget_line(
    payload: BudgetLineCreate,
    db: AsyncSession = Depends(get_db),
):
    line = BudgetLine(
        event_id=payload.event_id,
        job_id=payload.job_id,
        budget_period_id=payload.budget_period_id,
        category=payload.category,
        description=payload.description,
        budgeted_amount=payload.budgeted_amount,
        notes=payload.notes,
    )
    db.add(line)
    await db.flush()
    await db.refresh(line)
    return line


@router.get("/lines", response_model=list[BudgetLineResponse])
async def list_budget_lines(
    event_id: UUID | None = Query(None),
    job_id: UUID | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(BudgetLine).order_by(BudgetLine.created_at.desc())
    if event_id:
        q = q.where(BudgetLine.event_id == event_id)
    if job_id:
        q = q.where(BudgetLine.job_id == job_id)
    if category:
        q = q.where(BudgetLine.category == category)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/commitments", response_model=BudgetCommitmentResponse, status_code=201)
async def create_budget_commitment(
    payload: BudgetCommitmentCreate,
    db: AsyncSession = Depends(get_db),
):
    commit = BudgetCommitment(
        budget_line_id=payload.budget_line_id,
        purchase_invoice_id=payload.purchase_invoice_id,
        sales_invoice_id=payload.sales_invoice_id,
        amount=payload.amount,
        source_type=payload.source_type,
        source_id=payload.source_id,
    )
    db.add(commit)
    line_result = await db.execute(
        select(BudgetLine).where(BudgetLine.id == payload.budget_line_id)
    )
    line = line_result.scalar_one_or_none()
    if line:
        agg = await db.scalar(
            select(func.coalesce(func.sum(BudgetCommitment.amount), 0)).where(
                BudgetCommitment.budget_line_id == payload.budget_line_id
            )
        ) or 0
        line.committed_amount = float(agg)
    await db.flush()
    await db.refresh(commit)
    return commit


@router.get("/commitments", response_model=list[BudgetCommitmentResponse])
async def list_budget_commitments(
    budget_line_id: UUID | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(BudgetCommitment).order_by(BudgetCommitment.created_at.desc())
    if budget_line_id:
        q = q.where(BudgetCommitment.budget_line_id == budget_line_id)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/migrate-create-tables")
async def migrate_create_tables(db: AsyncSession = Depends(get_db)):
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS budget_periods (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                fiscal_year INTEGER NOT NULL,
                quarter INTEGER,
                month INTEGER,
                label VARCHAR(50) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_closed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS budget_lines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                event_id UUID REFERENCES events(id) NOT NULL,
                job_id UUID REFERENCES jobs(id) NOT NULL,
                budget_period_id UUID REFERENCES budget_periods(id),
                category VARCHAR(50) NOT NULL,
                description VARCHAR(255),
                budgeted_amount NUMERIC(15,2) NOT NULL,
                actual_amount NUMERIC(15,2) DEFAULT 0,
                committed_amount NUMERIC(15,2) DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS budget_commitments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                budget_line_id UUID REFERENCES budget_lines(id) NOT NULL,
                purchase_invoice_id UUID REFERENCES purchase_invoices(id),
                sales_invoice_id UUID REFERENCES sales_invoices(id),
                amount NUMERIC(15,2) NOT NULL,
                source_type VARCHAR(20),
                source_id UUID,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))
    return {"tables_created": ["budget_periods", "budget_lines", "budget_commitments"]}
