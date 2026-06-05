from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_safe import MOCK_DASHBOARD
from app.services.dashboard_service import get_dashboard_summary
from app.schemas.dashboard import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)):
    if db is None:
        return DashboardSummary(**MOCK_DASHBOARD)
    return get_dashboard_summary(db)
