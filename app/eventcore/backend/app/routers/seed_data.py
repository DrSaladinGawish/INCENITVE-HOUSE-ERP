"""Seed and verify endpoints for test data validation."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.scripts.seed_test_data import seed_all, verify_gates

router = APIRouter(prefix="/api/v1/seed", tags=["Seed Data"])


@router.post("/run")
async def run_seed(db: AsyncSession = Depends(get_db)):
    result = await seed_all(db)
    if result.get("status") == "skipped":
        return result
    gates = await verify_gates(db)
    return {"seed": result, "gates": gates}


@router.post("/run-all")
async def run_seed_and_verify(db: AsyncSession = Depends(get_db)):
    result = await seed_all(db)
    gates = await verify_gates(db)
    return {"seed": result, "gates": gates}


@router.get("/verify")
async def get_verification(db: AsyncSession = Depends(get_db)):
    gates = await verify_gates(db)
    return {"gates": gates}
