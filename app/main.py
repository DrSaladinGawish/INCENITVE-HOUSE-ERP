from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import SyncSessionLocal
from app.logging_config import setup_logging
from app.middleware.request_id import RequestIDMiddleware
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
)
from app.routers.neural import ai_api as neural_router
from app.routers.neural_live import router as neural_live_router
from app.routers import documents as documents_router

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
app.include_router(pages_router.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.VERSION}
