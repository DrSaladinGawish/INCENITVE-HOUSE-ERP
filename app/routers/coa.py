import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import COAAccountCreate, COAAccountResponse
from app.models.models import COAMaster, AuditTrail

router = APIRouter(prefix="/api/v1/coa", tags=["coa"])


@router.get("/")
async def list_coa(categ_key: str = "", search: str = "", limit: int = 500, offset: int = 0, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    q = select(COAMaster)
    if categ_key: q = q.where(COAMaster.categ_key == categ_key)
    if search: q = q.where(COAMaster.acc_name.ilike(f"%{search}%") | COAMaster.acc_key.ilike(f"%{search}%"))
    q = q.order_by(COAMaster.acc_key).offset(offset).limit(limit)
    result = await db.execute(q)
    return [{"id": r.id, "acc_key": r.acc_key, "acc_name": r.acc_name, "acc_name_ar": r.acc_name_ar, "categ_key": r.categ_key, "acc_type": r.acc_type, "is_active": r.is_active} for r in result.all()]


@router.get("/{acc_id}", response_model=COAAccountResponse)
async def get_coa(acc_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    r = await db.get(COAMaster, acc_id)
    if not r: raise HTTPException(status_code=404, detail="Account not found")
    return r


@router.post("/", response_model=COAAccountResponse)
async def create_coa(data: COAAccountCreate, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    r = COAMaster(**data.model_dump())
    db.add(r); await db.commit(); await db.refresh(r)
    db.add(AuditTrail(table_name="coa_master", record_id=r.id, action="CREATE", new_values=data.model_dump(), changed_by=user["username"], changed_at=datetime.datetime.utcnow()))
    await db.commit()
    return r


@router.get("/categories/list")
async def list_categories(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    result = await db.execute(select(COAMaster.categ_key).distinct().where(COAMaster.categ_key.isnot(None)).order_by(COAMaster.categ_key))
    return [row[0] for row in result.all()]


@router.get("/types/list")
async def list_types(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    result = await db.execute(select(COAMaster.acc_type).distinct().where(COAMaster.acc_type.isnot(None)).order_by(COAMaster.acc_type))
    return [row[0] for row in result.all()]
