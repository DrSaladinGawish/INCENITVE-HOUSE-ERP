from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.job import Job
from app.models.job_line_item import JobLineItem
from app.models.client import Client
from app.schemas.job import JobCreate, JobResponse, JobPNLResponse
from app.utils.job_code import generate_job_code

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(payload: JobCreate, db: AsyncSession = Depends(get_db)):
    year = 25

    job_code = await generate_job_code(db, year, payload.client_id)

    job = Job(
        job_code=job_code,
        year=year,
        client_id=payload.client_id,
        sequence=int(job_code.split(".")[-1]),
        event_name=payload.event_name,
        description=payload.description,
        margin_target=payload.margin_target,
    )
    if payload.event_dates:
        pass

    db.add(job)
    await db.flush()
    await db.refresh(job)

    from app.eventcore_job_hook import notify_bio_erp_new_job
    try:
        await notify_bio_erp_new_job(job.id, job.event_name, job.client_id)
    except Exception:
        pass

    return job


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    client_id: UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(Job).order_by(Job.created_at.desc())
    if client_id:
        q = q.where(Job.client_id == client_id)
    if status:
        q = q.where(Job.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/{job_id}/pnl", response_model=JobPNLResponse)
async def get_job_pnl(job_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    # REVENUE: Sales invoice amounts (accrual basis)
    from app.models.sales_invoice import SalesInvoice as SI
    si_rev = await db.scalar(
        select(func.coalesce(func.sum(SI.total_amount), 0))
        .where(SI.job_id == job_id)
    ) or 0

    # COST: Purchase invoice amounts (accrual) + payment voucher amounts (cash)
    from app.models.purchase_invoice import PurchaseInvoice as PI
    pi_cost = await db.scalar(
        select(func.coalesce(func.sum(PI.total_amount), 0))
        .where(PI.job_id == job_id)
    ) or 0

    from app.models.payment_voucher import PaymentVoucher as PV
    pv_cost = await db.scalar(
        select(func.coalesce(func.sum(PV.amount), 0))
        .where(PV.job_id == job_id, PV.status == "paid")
    ) or 0

    total_revenue = float(si_rev)
    total_cost = float(pi_cost) + float(pv_cost)
    gross_profit = total_revenue - total_cost
    margin_pct = round(gross_profit / total_revenue * 100, 2) if total_revenue > 0 else 0.0

    return JobPNLResponse(
        job_id=job.id,
        job_code=job.job_code,
        event_name=job.event_name,
        total_revenue=total_revenue,
        total_cost=total_cost,
        gross_profit=gross_profit,
        margin_pct=margin_pct,
        revenue_by_category=[],
        cost_by_category=[{"source": "pi_accrual", "total_amount": float(pi_cost)},
                          {"source": "pv_cash", "total_amount": float(pv_cost)}],
    )
