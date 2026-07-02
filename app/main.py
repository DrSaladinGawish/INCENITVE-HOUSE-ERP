import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, get_session, init_db
from app.deep_health import DeepHealthChecker
# Safe-import eventcore_bridge (corrupted file)
try:
    from app.eventcore_bridge import router as ec_proxy_router, start_eventcore, shutdown_client, stop_eventcore
except Exception:
    logging.warning("eventcore_bridge import failed — using placeholders")
    ec_proxy_router = APIRouter()
    @ec_proxy_router.get("/__unavailable", include_in_schema=False)
    def _ec_unavailable():
        return {"status": "unavailable", "module": "app.eventcore_bridge"}
    async def start_eventcore(): pass
    async def shutdown_client(): pass
    async def stop_eventcore(): pass
try:
    from app.logging_config import setup_logging
except Exception:
    logging.warning("logging_config import failed — using basicConfig fallback")
    def setup_logging():
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        return logging.getLogger(__name__)
try:
    from app.meta_layer import MetaLayerInjectorMiddleware, meta_router, meta_v2_router
except Exception:
    logging.warning("meta_layer import failed — using placeholders")
    class MetaLayerInjectorMiddleware:
        def __init__(self, app): self.app = app
        async def __call__(self, scope, receive, send):
            await self.app(scope, receive, send)
    meta_router = APIRouter()
    @meta_router.get("/__unavailable", include_in_schema=False)
    def _meta_unavailable(): return {"status": "unavailable", "module": "app.meta_layer"}
    meta_v2_router = APIRouter()
    @meta_v2_router.get("/__unavailable", include_in_schema=False)
    def _metav2_unavailable(): return {"status": "unavailable", "module": "app.meta_layer"}
try:
    from app.middleware.request_id import RequestIDMiddleware
except Exception:
    logging.warning("RequestIDMiddleware import failed — using placeholder")
    class RequestIDMiddleware:
        def __init__(self, app): self.app = app
        async def __call__(self, scope, receive, send):
            await self.app(scope, receive, send)

try:
    from app.middleware.security_headers import SecurityHeadersMiddleware
except Exception:
    logging.warning("SecurityHeadersMiddleware import failed — using placeholder")
    class SecurityHeadersMiddleware:
        def __init__(self, app): self.app = app
        async def __call__(self, scope, receive, send):
            await self.app(scope, receive, send)
from app.rate_limiter import setup_rate_limiter
from app.monitoring import MetricsMiddleware
from starlette.middleware.gzip import GZipMiddleware
from app.form_builder import form_builder_router
# ---------------------------------------------------------------------------
# Safe router loader — gracefully handle corrupted / missing routers
# ---------------------------------------------------------------------------
import importlib
from types import SimpleNamespace

_log_safe = logging.getLogger(__name__)


def _safe_module(module_path: str):
    """Import a router module; return SimpleNamespace(router=placeholder) on failure."""
    try:
        return importlib.import_module(module_path)
    except Exception as e:
        _log_safe.warning("Router load failed: %s — %s", module_path, str(e)[:120])
        r = APIRouter()
        @r.get("/__unavailable", include_in_schema=False)
        def _unavailable_placeholder():
            return {"status": "unavailable", "module": module_path}
        return SimpleNamespace(router=r)


def _safe_router(module_path: str, attr: str = "router"):
    """Import a router attribute; return placeholder APIRouter on failure."""
    try:
        return getattr(importlib.import_module(module_path), attr)
    except Exception as e:
        _log_safe.warning("Router load failed: %s — %s", module_path, str(e)[:120])
        r = APIRouter()
        @r.get("/__unavailable", include_in_schema=False)
        def _unavailable_placeholder():
            return {"status": "unavailable", "module": module_path}
        return r


ai_router = _safe_module("app.routers.ai_router")
auth_router = _safe_module("app.routers.auth_router")
bnk_router = _safe_module("app.routers.bnk_router")
dashboard_router = _safe_module("app.routers.dashboard_router")
evn_router = _safe_module("app.routers.evn_router")
export_router = _safe_module("app.routers.export_router")
financial_reports = _safe_module("app.routers.financial_reports")
gl_router = _safe_module("app.routers.gl_router")
import_router = _safe_module("app.routers.import_router")
intelligence_router = _safe_module("app.routers.intelligence_router")
pages_router = _safe_module("app.routers.pages_router")
pur_router = _safe_module("app.routers.pur_router")
sal_router = _safe_module("app.routers.sal_router")
documents_router = _safe_module("app.routers.documents")

appraisal_router = _safe_router("app.routers.appraisal_router")
archive_router = _safe_router("app.routers.archive_router")
backup_router = _safe_router("app.routers.backup_router")
bio_doctor_router = _safe_router("app.routers.bio_doctor")
budgeting_router = _safe_router("app.routers.budgeting")
bulk_router = _safe_router("app.routers.bulk_router")
contract_router = _safe_router("app.routers.contract_router")
crm_router = _safe_router("app.routers.crm")
e_invoice_router = _safe_router("app.routers.e_invoice")
event_budget_router = _safe_router("app.routers.event_budget_router")
exec_dashboard_router = _safe_router("app.routers.executive_dashboard_router")
executive_misc_router = _safe_router("app.routers.executive_misc_router")
financial_forms_router = _safe_router("app.routers.financial_forms_router")
financial_misc_router = _safe_router("app.routers.financial_misc_router")
fixed_assets_router = _safe_router("app.routers.fixed_assets")
fx_router = _safe_router("app.routers.fx_router")
hub_router = _safe_router("app.routers.hub_router")
inventory_router = _safe_router("app.routers.inventory")
kpi_router = _safe_router("app.routers.kpi_router")
launcher_router = _safe_router("app.routers.launcher_router")
meta_forms_router = _safe_router("app.routers.meta_router")
neural_router = _safe_module("app.routers.neural.ai_api")
neural_live_router = _safe_router("app.routers.neural_live")
operations_forms_router = _safe_router("app.routers.operations_forms_router")
operations_misc_router = _safe_router("app.routers.operations_misc_router")
payroll_router = _safe_router("app.routers.payroll")
people_misc_router = _safe_router("app.routers.people_misc_router")
procurement_forms_router = _safe_router("app.routers.procurement_forms_router")
procurement_misc_router = _safe_router("app.routers.procurement_misc_router")
pr_router = _safe_router("app.routers.purchase_requisition_router")
hscode_router = _safe_router("app.routers.hs.hscode_router")
rag_router = _safe_router("app.routers.rag_router")
reports_v2_router = _safe_router("app.routers.reports_router_v2")
revenue_forms_router = _safe_router("app.routers.revenue_forms_router")
revenue_misc_router = _safe_router("app.routers.revenue_misc_router")
standalone_forms_router = _safe_router("app.routers.standalone_forms")
system_misc_router = _safe_router("app.routers.system_misc_router")
venue_router = _safe_router("app.routers.venue_router")
workflow_router = _safe_router("app.routers.workflow")
from app.secure_config import get_secure_cors_origins, run_security_checks

log = setup_logging()


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown (non-blocking DB check)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("%s starting on port %s ...", settings.APP_NAME, settings.PORT)
    try:
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(loop.run_in_executor(None, _check_db), timeout=5.0)
    except TimeoutError:
        log.warning("Database connection timed out — starting in fallback mode")
    except Exception as e:
        log.warning("Database connection warning: %s", e)
    try:
        from app.monitoring import setup_multiprocess_metrics
        setup_multiprocess_metrics()
    except Exception as e:
        log.warning("Prometheus multiprocess setup failed: %s", e)
    run_security_checks()
    log.info("Initializing database tables...")
    init_db()
    log.info("Seeding form definitions...")
    try:
        from app.form_builder.seed import seed_forms
        from app.database import get_session
        session = get_session()
        if session:
            seed_forms(session)
            session.close()
    except Exception as e:
        log.warning("Form seed skipped: %s", e)
    log.info("Starting EventCore bridge...")
    try:
        await asyncio.wait_for(start_eventcore(), timeout=6.0)
    except TimeoutError:
        log.warning("EventCore start timed out — continuing without it")
    except Exception as e:
        log.warning("EventCore start failed: %s", e)
    # Start ETL scheduler
    try:
        from app.services.scheduler_service import start_scheduler
        await start_scheduler(interval_minutes=60)
    except Exception as e:
        log.warning("ETL scheduler start failed: %s", e)
    # Cache warming
    try:
        from app.services import chroma_rag_service
        from app.services.cache_warmer import CacheWarmer, warm_kpi_views, warm_master_tables, warm_rag_index
        warmer = CacheWarmer()
        warmer.register(lambda: warm_kpi_views(get_session), "kpi_views")
        warmer.register(lambda: warm_master_tables(get_session), "master_tables")
        warmer.register(lambda: warm_rag_index(chroma_rag_service), "rag_index")
        await warmer.warm_all(timeout=15.0)
    except Exception as e:
        log.warning("Cache warming skipped: %s", e)
    # Arabic LLM init
    try:
        from app.services import chroma_rag_service as crs
        from app.services.arabic_llm_chat import get_arabic_chat
        get_arabic_chat(rag_service=crs)
        log.info("Arabic LLM chat service initialized")
    except Exception as e:
        log.warning("Arabic LLM init skipped: %s", e)
    yield
    log.info("%s shutting down ...", settings.APP_NAME)
    await stop_eventcore()
    await shutdown_client()
    try:
        from app.services.scheduler_service import stop_scheduler
        await stop_scheduler()
    except Exception as e:
        log.warning("ETL scheduler shutdown skipped: %s", e)


def _check_db():
    from app.db_safe import check_sql_available
    check_sql_available(reset=True)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
setup_rate_limiter(app, requests_per_minute=100)

app.add_middleware(MetricsMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_secure_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetaLayerInjectorMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


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
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="frontend_assets")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

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
app.include_router(bulk_router)
app.include_router(pages_router.router)
app.include_router(intelligence_router.router)
app.include_router(meta_router)
app.include_router(meta_v2_router)
app.include_router(meta_forms_router)
app.include_router(import_router.router)
app.include_router(financial_reports.router)
app.include_router(e_invoice_router)
app.include_router(workflow_router)
app.include_router(reports_v2_router)
app.include_router(archive_router)
app.include_router(fx_router)
app.include_router(inventory_router)
app.include_router(payroll_router)
app.include_router(crm_router)
app.include_router(budgeting_router)
app.include_router(fixed_assets_router)
app.include_router(backup_router)
app.include_router(bio_doctor_router)
app.include_router(launcher_router)
app.include_router(hub_router)
app.include_router(standalone_forms_router)
app.include_router(financial_forms_router)
app.include_router(revenue_forms_router)
app.include_router(procurement_forms_router)
app.include_router(operations_forms_router)
app.include_router(ec_proxy_router)
app.include_router(pr_router)
app.include_router(venue_router)
app.include_router(contract_router)
app.include_router(appraisal_router)
app.include_router(event_budget_router)
app.include_router(kpi_router)
app.include_router(form_builder_router, prefix="/api/v1/forms")
app.include_router(financial_misc_router)
app.include_router(revenue_misc_router)

# ---------------------------------------------------------------------------
# MCP (Model Context Protocol) — SSE server for Claude Desktop
# ---------------------------------------------------------------------------
try:
    from app.mcp.server import get_mcp_sse_app
    app.mount("/mcp", get_mcp_sse_app())
    log.info("MCP server mounted at /mcp/sse — Claude Desktop can connect via http://localhost:9001/mcp/sse")
except Exception:
    log.warning("MCP server import failed — skipping")
    @app.get("/mcp/__unavailable", include_in_schema=False)
    def _mcp_unavailable():
        return {"status": "unavailable", "module": "app.mcp.server"}
app.include_router(procurement_misc_router)
app.include_router(operations_misc_router)
app.include_router(people_misc_router)
app.include_router(system_misc_router)
app.include_router(executive_misc_router)
app.include_router(exec_dashboard_router)
app.include_router(hscode_router)
app.include_router(rag_router)

financial_api_router = _safe_router("app.routers.financial_api")
app.include_router(financial_api_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    from app.database import _get_mysql_session
    from app.db_safe import check_sql_available
    db_status = "offline"
    db_type = "none"
    pnr_count = 0
    try:
        conn = get_session()
        if conn is not None:
            conn.execute(text("SELECT 1"))
            is_mysql = not check_sql_available()
            db_status = "ok"
            db_type = "mysql" if is_mysql else "sqlserver"
            try:
                from sqlalchemy import func, select

                from app.models.ihe_models import PNRMaster
                pnr_count = conn.execute(select(func.count(PNRMaster.PNRNumber))).scalar() or 0
            except Exception:
                log.warning("Suppressed error", exc_info=True)
            conn.close()
    except Exception:
        log.warning("Suppressed error", exc_info=True)
    if db_status == "offline":
        try:
            conn = _get_mysql_session()
            if conn is not None:
                conn.execute(text("SELECT 1"))
                db_status = "ok"
                db_type = "mysql"
                try:
                    from sqlalchemy import func, select

                    from app.models.ihe_models import PNRMaster
                    pnr_count = conn.execute(select(func.count(PNRMaster.PNRNumber))).scalar() or 0
                except Exception:
                    log.warning("Suppressed error", exc_info=True)
                conn.close()
        except Exception:
            log.warning("Suppressed error", exc_info=True)
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.VERSION, "database": db_status, "db_type": db_type, "total_pnrs": pnr_count}


@app.get("/health/deep")
async def deep_health():
    return await DeepHealthChecker().check_all()


@app.get("/metrics")
async def metrics():
    from app.monitoring import generate_metrics
    from fastapi.responses import Response
    return Response(content=generate_metrics(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# Search endpoint
# ---------------------------------------------------------------------------
@app.get("/api/search")
def global_search(q: str = "", db: Session = Depends(get_db)):
    from sqlalchemy import func, select

    from app.models.ihe_models import Client, PNRMaster, Vendor
    results = {"pnrs": 0, "clients": 0, "vendors": 0}
    if not q.strip():
        return results
    like = f"%{q.strip()}%"
    try:
        pnr_count = db.execute(select(func.count(PNRMaster.PNRNumber)).where(PNRMaster.PNRNumber.like(like))).scalar() or 0
        results["pnrs"] = pnr_count
    except Exception:
        log.warning("Suppressed error", exc_info=True)
    try:
        client_count = db.execute(select(func.count(Client.ClientCode)).where(Client.ClientName.like(like))).scalar() or 0
        results["clients"] = client_count
    except Exception:
        log.warning("Suppressed error", exc_info=True)
    try:
        vendor_count = db.execute(select(func.count(Vendor.VendorCode)).where(Vendor.VendorName.like(like))).scalar() or 0
        results["vendors"] = vendor_count
    except Exception:
        log.warning("Suppressed error", exc_info=True)
    return results


# ---------------------------------------------------------------------------
# SPA fallback — serve React app at /, /financial, /revenue, etc.
# Only activates when frontend/dist/index.html exists (built React app)
# ---------------------------------------------------------------------------
frontend_index = frontend_dist / "index.html"
if frontend_dist.is_dir() and frontend_index.is_file():
    from fastapi.responses import HTMLResponse

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Don't interfere with API routes
        if full_path.split("/")[0] in ("api", "health", "docs", "openapi", "static", "assets"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        return HTMLResponse(frontend_index.read_bytes())
else:
    from fastapi.responses import JSONResponse


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001, reload=False)
