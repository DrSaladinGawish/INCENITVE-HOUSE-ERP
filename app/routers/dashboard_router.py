from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_safe import MOCK_DASHBOARD
from app.services.dashboard_service import get_dashboard_summary, get_monthly_data
from app.schemas.dashboard import DashboardSummary
from app.pdf_generator import generate_dashboard_pdf, generate_list_pdf
from app.excel_generator import generate_excel, generate_csv

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)):
    if db is None:
        return DashboardSummary(**MOCK_DASHBOARD)
    return get_dashboard_summary(db)


@router.get("/export")
def export_dashboard(format: str = Query("pdf", regex="^(pdf|xlsx|csv)$"), db: Session = Depends(get_db)):
    if db is None:
        summary_data = MOCK_DASHBOARD
    else:
        summary_data = get_dashboard_summary(db).model_dump()
    monthly = get_monthly_data(db) if db else []

    if format == "pdf":
        buf = generate_dashboard_pdf(summary_data, monthly)
        return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=dashboard.pdf"})
    elif format == "xlsx":
        monthly_rows = [[m["month"], m["revenue"], m["expenses"], m["net"]] for m in monthly]
        sheets = [
            {"name": "Dashboard", "headers": ["Metric", "Value"], "rows": [[k, str(v)] for k, v in summary_data.items()]},
            {"name": "Monthly", "headers": ["Month", "Revenue", "Expenses", "Net"], "rows": monthly_rows},
        ]
        buf = generate_excel(sheets)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=dashboard.xlsx"})
    else:
        rows = [[k, str(v)] for k, v in summary_data.items()]
        csv = generate_csv(["Metric", "Value"], rows)
        return StreamingResponse(iter([csv]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=dashboard.csv"})


@router.get("/monthly")
def monthly_data(db: Session = Depends(get_db)):
    if db is None:
        return []
    return get_monthly_data(db)
