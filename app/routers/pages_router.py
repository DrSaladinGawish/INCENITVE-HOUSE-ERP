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


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/evn", response_class=HTMLResponse)
def pnr_list_page(request: Request):
    return templates.TemplateResponse("pnr_list.html", {"request": request})


@router.get("/evn/new", response_class=HTMLResponse)
def pnr_new_page(request: Request):
    return templates.TemplateResponse("pnr_form.html", {
        "request": request, "title": "New PNR", "subtitle": "Create a new Program Notification Record", "pnr": None
    })


@router.get("/evn/{pnr_number}", response_class=HTMLResponse)
def pnr_detail_page(request: Request, pnr_number: str, db: Session = Depends(get_db)):
    pnr = evn_service.get_pnr(db, pnr_number)
    if not pnr:
        return HTMLResponse(content="PNR not found", status_code=404)
    return templates.TemplateResponse("pnr_detail.html", {"request": request, "pnr": pnr})


@router.get("/evn/{pnr_number}/edit", response_class=HTMLResponse)
def pnr_edit_page(request: Request, pnr_number: str, db: Session = Depends(get_db)):
    pnr = evn_service.get_pnr(db, pnr_number)
    if not pnr:
        return HTMLResponse(content="PNR not found", status_code=404)
    return templates.TemplateResponse("pnr_form.html", {
        "request": request, "title": "Edit PNR - " + pnr_number,
        "subtitle": "Update Program Notification Record", "pnr": pnr
    })


@router.get("/sal", response_class=HTMLResponse)
def sales_page(request: Request):
    return templates.TemplateResponse("sales_list.html", {"request": request})


@router.get("/sal/new", response_class=HTMLResponse)
def sales_new_page(request: Request):
    return templates.TemplateResponse("sales_form.html", {
        "request": request, "title": "New Sales Invoice",
        "subtitle": "Create a new client invoice", "inv": None
    })


@router.get("/pur", response_class=HTMLResponse)
def purchases_page(request: Request):
    return templates.TemplateResponse("purchases_list.html", {"request": request})


@router.get("/pur/new", response_class=HTMLResponse)
def purchases_new_page(request: Request):
    return templates.TemplateResponse("purchases_form.html", {
        "request": request, "title": "New Purchase Voucher",
        "subtitle": "Create a new vendor payment voucher", "vch": None
    })


@router.get("/bnk", response_class=HTMLResponse)
def banking_page(request: Request):
    return templates.TemplateResponse("banking_list.html", {"request": request})


@router.get("/bnk/new", response_class=HTMLResponse)
def banking_new_page(request: Request):
    return templates.TemplateResponse("banking_form.html", {
        "request": request, "title": "New Bank Transaction",
        "subtitle": "Record a deposit, withdrawal, or transfer", "vch": None
    })


@router.get("/gl", response_class=HTMLResponse)
def gl_page(request: Request):
    return templates.TemplateResponse("gl_list.html", {"request": request})


@router.get("/gl/new", response_class=HTMLResponse)
def gl_new_page(request: Request):
    return templates.TemplateResponse("gl_form.html", {
        "request": request, "title": "New Journal Voucher",
        "subtitle": "Create a general ledger journal entry", "vch": None
    })


@router.get("/documents", response_class=HTMLResponse)
def documents_page(request: Request):
    return templates.TemplateResponse("documents.html", {"request": request})


@router.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request):
    return templates.TemplateResponse("report_builder.html", {"request": request})


@router.get("/intelligence", response_class=HTMLResponse)
def intelligence_home(request: Request):
    return templates.TemplateResponse("audit_log.html", {"request": request})


@router.get("/intelligence/audit", response_class=HTMLResponse)
def audit_page(request: Request):
    return templates.TemplateResponse("audit_log.html", {"request": request})


@router.get("/intelligence/or", response_class=HTMLResponse)
def or_workbench_page(request: Request):
    return templates.TemplateResponse("or_workbench.html", {"request": request})


@router.get("/intelligence/scm", response_class=HTMLResponse)
def scm_workbench_page(request: Request):
    return templates.TemplateResponse("scm_workbench.html", {"request": request})


@router.get("/intelligence/backup", response_class=HTMLResponse)
def backup_page(request: Request):
    return templates.TemplateResponse("backup.html", {"request": request})


@router.get("/intelligence/neural", response_class=HTMLResponse)
def neural_page(request: Request):
    return templates.TemplateResponse("neural_panel.html", {"request": request})