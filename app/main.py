from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SyncSessionLocal, get_db
from app.logging_config import setup_logging
from app.middleware.request_id import RequestIDMiddleware
from app.meta_layer import MetaLayerInjectorMiddleware, meta_router, meta_v2_router
from app.routers import (
    auth_router,
    bnk_router,
    sal_router,
    pur_router,
    evn_router,
    gl_router,
    dashboard_router,
    pages_router,
    ai_router,
    intelligence_router,
)
from app.routers.neural import ai_api as neural_router
from app.routers.neural_live import router as neural_live_router
from app.routers import documents as documents_router
from app.routers import export_router
from app.routers import financial_reports
from app.routers import e_invoice_router
from app.routers import workflow_router
from app.routers.reports_router_v2 import router as reports_v2_router

log = setup_logging()


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("%s starting on port %s ...", settings.APP_NAME, settings.PORT)
    try:
        conn = SyncSessionLocal()
        conn.execute(
            conn.bind.dialect.statement_compiler(conn.bind.dialect, None)
            .__class__.__module__
        )
        log.info("Database connection OK (SQL Server)")
        conn.close()
    except Exception as e:
        log.warning("Database connection warning: %s", e)
    yield
    log.info("%s shutting down ...", settings.APP_NAME)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetaLayerInjectorMiddleware)


# ---------------------------------------------------------------------------
# Global exception handler (production-safe)
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please contact support."},
    )


# ---------------------------------------------------------------------------
# Static files & routers
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router.router)
app.include_router(bnk_router.router)
app.include_router(sal_router.router)
app.include_router(pur_router.router)
app.include_router(evn_router.router)
app.include_router(gl_router.router)
app.include_router(dashboard_router.router)
app.include_router(ai_router.router)
app.include_router(neural_router.router)
app.include_router(neural_live_router)
app.include_router(documents_router.router)
app.include_router(export_router.router)
app.include_router(pages_router.router)
app.include_router(intelligence_router.router)
app.include_router(meta_router)
app.include_router(meta_v2_router)
app.include_router(financial_reports.router)
app.include_router(e_invoice_router.router)
app.include_router(workflow_router.router)
app.include_router(reports_v2_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    from app.database import SyncSessionLocal
    from sqlalchemy import text, select, func
    from app.models.ihe_models import PNRMaster
    db_status = "unknown"
    pnr_count = 0
    try:
        conn = SyncSessionLocal()
        conn.execute(text("SELECT 1"))
        db_status = "ok"
        pnr_count = conn.execute(select(func.count(PNRMaster.PNRNumber))).scalar() or 0
        conn.close()
    except Exception:
        db_status = "error"
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.VERSION, "database": db_status, "total_pnrs": pnr_count}


# ---------------------------------------------------------------------------
# Search endpoint
# ---------------------------------------------------------------------------
@app.get("/api/search")
def global_search(q: str = "", db: Session = Depends(get_db)):
    from app.models.ihe_models import PNRMaster, Client, Vendor
    from sqlalchemy import select, func
    results = {"pnrs": 0, "clients": 0, "vendors": 0}
    if not q.strip():
        return results
    like = f"%{q.strip()}%"
    try:
        pnr_count = db.execute(select(func.count(PNRMaster.PNRNumber)).where(PNRMaster.PNRNumber.like(like))).scalar() or 0
        results["pnrs"] = pnr_count
    except Exception:
        pass
    try:
        client_count = db.execute(select(func.count(Client.ClientCode)).where(Client.ClientName.like(like))).scalar() or 0
        results["clients"] = client_count
    except Exception:
        pass
    try:
        vendor_count = db.execute(select(func.count(Vendor.VendorCode)).where(Vendor.VendorName.like(like))).scalar() or 0
        results["vendors"] = vendor_count
    except Exception:
        pass
    return results
