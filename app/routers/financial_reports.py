from datetime import date
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import financial_reports_service as frs

router = APIRouter(prefix="/reports/financial", tags=["Financial Reports"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def reports_dashboard(request: Request):
    return templates.TemplateResponse("reports/financial/dashboard.html", {"request": request})


@router.get("/trial-balance", response_class=HTMLResponse)
def trial_balance_page(
    request: Request,
    as_of_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    data = frs.get_trial_balance(db, as_of_date)
    return templates.TemplateResponse("reports/financial/trial_balance.html", {"request": request, "data": data})


@router.get("/api/trial-balance")
def trial_balance_api(
    as_of_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    return frs.get_trial_balance(db, as_of_date)


@router.get("/profit-loss", response_class=HTMLResponse)
def profit_loss_page(
    request: Request,
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    data = frs.get_profit_loss(db, from_date, to_date)
    return templates.TemplateResponse("reports/financial/profit_loss.html", {"request": request, "data": data})


@router.get("/api/profit-loss")
def profit_loss_api(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return frs.get_profit_loss(db, from_date, to_date)


@router.get("/balance-sheet", response_class=HTMLResponse)
def balance_sheet_page(
    request: Request,
    as_of_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    data = frs.get_balance_sheet(db, as_of_date)
    return templates.TemplateResponse("reports/financial/balance_sheet.html", {"request": request, "data": data})


@router.get("/api/balance-sheet")
def balance_sheet_api(
    as_of_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    return frs.get_balance_sheet(db, as_of_date)


@router.get("/cash-flow", response_class=HTMLResponse)
def cash_flow_page(
    request: Request,
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    data = frs.get_cash_flow(db, from_date, to_date)
    return templates.TemplateResponse("reports/financial/cash_flow.html", {"request": request, "data": data})


@router.get("/api/cash-flow")
def cash_flow_api(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return frs.get_cash_flow(db, from_date, to_date)
