from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.database import init_db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.surgery_deps import AuthRequiredException, get_current_user
from app.routers import (
    jobs, purchase_invoices, bank_transactions, dashboard, quotations, sales_invoices,
    events, employees, accounts, vat, company, clients, vendors, bio_bridge, bio_sync,
    prescription_receiver, prescriptions_htmx, or_insights, pdf, categories,
    e_invoice, budget, seed_data, payment_vouchers, receipt_vouchers, data_quality, reports, audit,
    auth,
)

# Email service disabled by default in v1


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[Lifespan] {settings.app_name} v{settings.app_version} starting...")
    try:
        await init_db()
        print("[Lifespan] Database tables created")
    except Exception as e:
        print(f"[Lifespan] DB init warning: {e}")
    yield
    print(f"[Lifespan] {settings.app_name} shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="Job P&L-centric Incentive House ERP System — EventCore",
    version=settings.app_version,
    lifespan=lifespan,
    debug=settings.debug,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/ → project root
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class EventCoreCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        import uuid
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(EventCoreCorrelationMiddleware)


@app.exception_handler(AuthRequiredException)
async def auth_required_handler(request: Request, exc: AuthRequiredException):
    accept = request.headers.get("accept", "")
    is_htmx = request.headers.get("hx-request") is not None
    if is_htmx or "text/html" in accept:
        return RedirectResponse(url="/auth/login", status_code=302)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
    )


app.include_router(jobs.router)
app.include_router(purchase_invoices.router)
app.include_router(bank_transactions.router)
app.include_router(dashboard.router)
app.include_router(quotations.router)
app.include_router(sales_invoices.router)
app.include_router(events.router)
app.include_router(employees.router)
app.include_router(accounts.router)
app.include_router(vat.router)
app.include_router(company.router)
app.include_router(clients.router)
app.include_router(vendors.router)
app.include_router(bio_bridge.router)
app.include_router(bio_sync.router)
app.include_router(prescription_receiver.router)
app.include_router(prescriptions_htmx.router)
app.include_router(or_insights.router)
app.include_router(pdf.router)
app.include_router(categories.router)
app.include_router(e_invoice.router)
app.include_router(budget.router)
app.include_router(seed_data.router)
app.include_router(payment_vouchers.router)
app.include_router(receipt_vouchers.router)
app.include_router(data_quality.router)
app.include_router(reports.router)
app.include_router(auth.router)
app.include_router(audit.router)


@app.get("/dashboard")
async def dashboard_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "dashboard.html", {"request": request, "user": user})

@app.get("/events", response_class=HTMLResponse)
async def events_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "events/list.html", {"request": request, "user": user})

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "jobs/list.html", {"request": request, "user": user})

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail_page(
    job_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.job import Job
    from sqlalchemy import select
    try:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
    except Exception as e:
        return HTMLResponse(f"<html><body><h1>DB Error</h1><pre>{e}</pre></body></html>")
    if not job:
        # Debug: check how many jobs exist
        try:
            count_result = await db.execute(select(Job))
            all_jobs = count_result.scalars().all()
            return HTMLResponse(f"<html><body><h1>No Job Found</h1><p>ID: {job_id}</p><p>Total jobs: {len(all_jobs)}</p><p>Job IDs: {[str(j.id) for j in all_jobs[:5]]}</p></body></html>")
        except Exception as e2:
            return HTMLResponse(f"<html><body><h1>Count Error</h1><pre>{e2}</pre></body></html>")
    return templates.TemplateResponse(request, "jobs/detail.html", {"request": request, "user": user, "job": job})

@app.get("/debug/jobs-count")
async def debug_jobs_count(db: AsyncSession = Depends(get_db)):
    from app.models.job import Job
    from sqlalchemy import select
    result = await db.execute(select(Job))
    all_jobs = result.scalars().all()
    return {"total": len(all_jobs), "ids": [str(j.id) for j in all_jobs[:10]]}

@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "clients/list.html", {"request": request, "user": user})

@app.get("/vendors", response_class=HTMLResponse)
async def vendors_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "vendors/list.html", {"request": request, "user": user})

@app.get("/payment-vouchers", response_class=HTMLResponse)
async def pv_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "finance/payment_vouchers.html", {"request": request, "user": user})

@app.get("/receipt-vouchers", response_class=HTMLResponse)
async def rv_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "finance/receipt_vouchers.html", {"request": request, "user": user})

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "reports/index.html", {"request": request, "user": user})

@app.get("/data-quality", response_class=HTMLResponse)
async def dq_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(request, "data_quality/index.html", {"request": request, "user": user})


@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version, "app": settings.app_name}


@app.get("/api/v1/health/db")
async def db_health():
    import sqlite3
    db_path = r"D:\eventmanager-erp\backend\eventcore.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [r[0] for r in c.fetchall()]
    total = len(all_tables)
    active = 0
    total_rows = 0
    for t in all_tables:
        c.execute(f'SELECT count(*) FROM "{t}"')
        cnt = c.fetchone()[0]
        total_rows += cnt
        if cnt > 0:
            active += 1
    cats = c.execute("SELECT count(*) FROM categories").fetchone()[0]
    subs = c.execute("SELECT count(*) FROM sub_categories").fetchone()[0]
    bank_linked = c.execute("SELECT count(*) FROM bank_transactions WHERE linked_job_id IS NOT NULL").fetchone()[0]
    bank_total = c.execute("SELECT count(*) FROM bank_transactions").fetchone()[0]
    items = c.execute("SELECT count(*) FROM job_line_items").fetchone()[0]
    rev = c.execute("SELECT coalesce(sum(cast(total_amount as real)),0) FROM job_line_items WHERE type='sales'").fetchone()[0]
    cost = c.execute("SELECT coalesce(sum(cast(total_amount as real)),0) FROM job_line_items WHERE type='purchase'").fetchone()[0]
    conn.close()
    return {
        "total_tables": total,
        "active_tables": active,
        "total_rows": total_rows,
        "schema_pct": round(active / total * 100, 1),
        "categories": cats,
        "sub_categories": subs,
        "bank_linked_pct": round(bank_linked / bank_total * 100, 1) if bank_total else 0,
        "bank_linked": bank_linked,
        "bank_total": bank_total,
        "line_items": items,
        "total_revenue": round(float(rev), 2),
        "total_cost": round(float(cost), 2),
        "timestamp": str(datetime.now(timezone.utc)),
    }


@app.get("/")
async def root():
    return {"message": settings.app_name, "version": settings.app_version, "tagline": "The EVENTailors..."}



