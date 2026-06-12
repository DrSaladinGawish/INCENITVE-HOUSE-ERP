from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.category import Category, SubCategory
from app.models.job_line_item import JobLineItem
from app.models.job import Job
from app.schemas.category import CategoryResponse, CategoryCreate, SubCategoryResponse, SubCategoryCreate

router = APIRouter(prefix="/api/v1", tags=["Categories"])


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    return result.scalars().all()


@router.get("/categories/{category_name}", response_model=CategoryResponse)
async def get_category(category_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.name == category_name))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(404, "Category not found")
    return category


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(payload: CategoryCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Category).where(Category.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Category already exists")
    category = Category(**payload.model_dump())
    db.add(category)
    await db.flush()
    await db.refresh(category)
    return category


@router.post("/categories/{category_name}/sub-categories", response_model=SubCategoryResponse, status_code=201)
async def create_sub_category(category_name: str, payload: SubCategoryCreate, db: AsyncSession = Depends(get_db)):
    cat_result = await db.execute(select(Category).where(Category.name == category_name))
    if not cat_result.scalar_one_or_none():
        raise HTTPException(404, "Category not found")
    existing = await db.execute(select(SubCategory).where(SubCategory.id == payload.id))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Sub-category ID already exists")
    sub = SubCategory(id=payload.id, name=payload.name, category_name=category_name)
    db.add(sub)
    await db.flush()
    await db.refresh(sub)
    return sub


@router.get("/sub-categories", response_model=list[SubCategoryResponse])
async def list_sub_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubCategory).order_by(SubCategory.category_name, SubCategory.name))
    return result.scalars().all()


@router.get("/jobs/{job_id}/line-items")
async def list_job_line_items(job_id: UUID, db: AsyncSession = Depends(get_db)):
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(404, "Job not found")
    result = await db.execute(
        select(
            JobLineItem.id,
            JobLineItem.description,
            JobLineItem.category,
            JobLineItem.sub_category,
            JobLineItem.total_amount,
            JobLineItem.currency,
        ).where(JobLineItem.job_id == job_id)
    )
    items = result.all()
    return [
        {
            "id": str(item.id),
            "description": item.description,
            "category": item.category,
            "sub_category": item.sub_category,
            "total_amount": float(item.total_amount),
            "currency": item.currency,
        }
        for item in items
    ]
