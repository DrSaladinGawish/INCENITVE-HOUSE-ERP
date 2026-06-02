"""IncentiveHouse ERP v2.2.2 — FastAPI Application Entrypoint."""

import os
import time
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("incentivehouse")

from app.database import init_db, close_db
from app.routers import auth, events, sales, bnk, finance
from app.routers import clients, vendors, pnr, employees, reports
from app.routers import pipeline, petty_cash, coa, cheques, wht
from app.routers import vendor_performance, currency, pdf
from app.routers.dashboard_ui import router as dashboard_router

app = FastAPI(
    title="IncentiveHouse ERP",
    version="2.2.2",
    description="Event management and financial ERP system",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    logger.info("Starting IncentiveHouse ERP v2.2.2")
    await init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down IncentiveHouse ERP")
    await close_db()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.3f}s)")
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "path": request.url.path},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": request.url.path},
    )


app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(clients.router, prefix="/api/v1/clients")
app.include_router(vendors.router, prefix="/api/v1/vendors")
app.include_router(events.router, prefix="/api/v1/events")
app.include_router(pnr.router, prefix="/api/v1/pnr")
app.include_router(employees.router, prefix="/api/v1/employees")
app.include_router(sales.router, prefix="/api/v1/sales")
app.include_router(bnk.router, prefix="/api/v1/bnk")
app.include_router(finance.router, prefix="/api/v1/finance")
app.include_router(reports.router, prefix="/api/v1/reports")
app.include_router(pipeline.router)
app.include_router(petty_cash.router)
app.include_router(coa.router)
app.include_router(cheques.router)
app.include_router(wht.router)
app.include_router(vendor_performance.router)
app.include_router(currency.router)
app.include_router(pdf.router)
app.include_router(dashboard_router)

try:
    from app.or_module.sub_app import or_app
    app.mount("/api/v1/or", or_app)
    logger.info("OR module mounted at /api/v1/or")
except ImportError:
    logger.warning("OR module not found — skipping mount")


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.2.2",
        "timestamp": time.time(),
    }


@app.get("/ready")
async def readiness():
    try:
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "database": str(e)},
        )


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "9001"))
    cert = os.environ.get("SSL_CERT", "")
    key = os.environ.get("SSL_KEY", "")
    ssl_kwargs = {}
    if cert and key and os.path.exists(cert) and os.path.exists(key):
        ssl_kwargs = {"ssl_keyfile": key, "ssl_certfile": cert}
        protocol = "HTTPS"
    else:
        protocol = "HTTP"
    logger.info(f"Starting on {protocol}://{host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "info").lower(),
        reload=os.environ.get("DEBUG", "").lower() == "true",
        **ssl_kwargs,
    )
