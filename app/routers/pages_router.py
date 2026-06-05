from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import evn_service

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Pages"])


@router.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/evn", response_class=HTMLResponse)
def pnr_list_page(request: Request):
    return templates.TemplateResponse("pnr_list.html", {"request": request})


@router.get("/evn/{pnr_number}", response_class=HTMLResponse)
def pnr_detail_page(request: Request, pnr_number: str, db: Session = Depends(get_db)):
    pnr = evn_service.get_pnr(db, pnr_number)
    if not pnr:
        return HTMLResponse(content="PNR not found", status_code=404)
    return templates.TemplateResponse("pnr_detail.html", {"request": request, "pnr": pnr})


@router.get("/sal", response_class=HTMLResponse)
def sales_page(request: Request):
    return templates.TemplateResponse("sales_list.html", {"request": request})


@router.get("/pur", response_class=HTMLResponse)
def purchases_page(request: Request):
    return templates.TemplateResponse("purchases_list.html", {"request": request})


@router.get("/bnk", response_class=HTMLResponse)
def banking_page(request: Request):
    return templates.TemplateResponse("banking_list.html", {"request": request})


@router.get("/gl", response_class=HTMLResponse)
def gl_page(request: Request):
    return templates.TemplateResponse("gl_list.html", {"request": request})


@router.get("/documents", response_class=HTMLResponse)
def documents_page(request: Request):
    return templates.TemplateResponse("documents.html", {"request": request})


@router.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request):
    return templates.TemplateResponse("report_builder.html", {"request": request})
