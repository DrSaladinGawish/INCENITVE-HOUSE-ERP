"""OR sub-application for internal requests and approvals."""
from fastapi import FastAPI, APIRouter, Depends
from app.database import get_db
from app.routers.auth import get_current_user

or_app = FastAPI(title="OR Module", version="1.0.0")
router = APIRouter(tags=["or"])


@router.get("/health")
async def or_health():
    return {"status": "ok", "module": "or"}


@router.get("/requests")
async def list_or_requests(db=Depends(get_db)):
    return {"detail": "OR module stub", "endpoints": 19}


or_app.include_router(router)
