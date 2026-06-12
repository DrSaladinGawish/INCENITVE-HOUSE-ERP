from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.quotation import Quotation, QuotationLineItem
from app.schemas.quotation import QuotationCreate, QuotationResponse

router = APIRouter(prefix="/api/v1/quotations", tags=["Quotations"])


@router.post("", response_model=QuotationResponse, status_code=201)
async def create_quotation(payload: QuotationCreate, db: AsyncSession = Depends(get_db)):
    q = Quotation(**payload.model_dump())
    db.add(q)
    await db.flush()
    await db.refresh(q)
    return q


@router.get("", response_model=list[QuotationResponse])
async def list_quotations(
    client_id: UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(Quotation).order_by(Quotation.created_at.desc())
    if client_id:
        q = q.where(Quotation.client_id == client_id)
    if status:
        q = q.where(Quotation.status == status)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{quotation_id}", response_model=QuotationResponse)
async def get_quotation(quotation_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Quotation).where(Quotation.id == quotation_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(404, "Quotation not found")
    return q


@router.patch("/{quotation_id}/convert")
async def convert_quotation_to_job(
    quotation_id: UUID,
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quotation).where(Quotation.id == quotation_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(404, "Quotation not found")
    q.converted_to_job_id = job_id
    q.status = "converted"
    await db.flush()
    return {"status": "converted", "quotation_id": str(quotation_id), "job_id": str(job_id)}
