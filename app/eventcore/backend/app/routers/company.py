from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.company_profile import CompanyProfile
from app.schemas.company_profile import CompanyProfileCreate, CompanyProfileResponse

router = APIRouter(prefix="/api/v1/company", tags=["Company"])


@router.post("/profile", response_model=CompanyProfileResponse, status_code=201)
async def create_company_profile(payload: CompanyProfileCreate, db: AsyncSession = Depends(get_db)):
    cp = CompanyProfile(**payload.model_dump())
    db.add(cp)
    await db.flush()
    await db.refresh(cp)
    return cp


@router.get("/profile", response_model=CompanyProfileResponse)
async def get_company_profile(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompanyProfile).limit(1))
    cp = result.scalar_one_or_none()
    if not cp:
        raise HTTPException(404, "Company profile not found. Create one first.")
    return cp


@router.put("/profile", response_model=CompanyProfileResponse)
async def update_company_profile(payload: CompanyProfileCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompanyProfile).limit(1))
    cp = result.scalar_one_or_none()
    if not cp:
        cp = CompanyProfile(**payload.model_dump())
        db.add(cp)
    else:
        for key, val in payload.model_dump().items():
            setattr(cp, key, val)
    await db.flush()
    await db.refresh(cp)
    return cp
