import os
import atexit
import logging
import shutil
import time

# ---------------------------------------------------------------------------
# CRITICAL: PROMETHEUS_MULTIPROC_DIR must be set BEFORE prometheus_client is
# imported.  The client reads this env var at import time in values.py to
# decide between MultiProcessValue (file-backed per-worker) and plain
# in-memory storage.  Setting it after import has zero effect — all
# Counter/Histogram/Gauge objects are already locked into single-process mode.
# ---------------------------------------------------------------------------
from app.config import settings
os.environ["prometheus_multiproc_dir"] = str(settings.PROMETHEUS_MULTIPROC_DIR)

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from prometheus_client import multiprocess
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger(__name__)

mp_dir = os.environ["prometheus_multiproc_dir"]

# ---------------------------------------------------------------------------
# Metrics definitions
# These are created per-worker.  At scrape time, MultiProcessCollector reads
# .db files from mp_dir and aggregates across all live workers.
# ---------------------------------------------------------------------------

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Gauge — NOT Counter — because this tracks a live count (up and down).
# multiprocess_mode='livesum' gives a single total across all workers;
# the default 'all' would expose one time series per PID.
ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Currently active requests",
    ["method"],
    multiprocess_mode="livesum",
)


def setup_multiprocess_metrics():
    """Initialize the multiprocess metrics directory.

    Called once at app startup (FastAPI lifespan).  Cleans stale .db files
    from previous runs that could silently inflate counters.
    """
    os.makedirs(mp_dir, exist_ok=True)

    # Remove stale .db files left by crashed workers.
    # Without a uvicorn child_exit hook (Gunicorn has one, uvicorn doesn't),
    # no mechanism calls mark_process_dead() after a hard kill — so we
    # aggressively clean at startup instead.
    for f in os.listdir(mp_dir):
        if f.endswith(".db"):
            try:
                os.remove(os.path.join(mp_dir, f))
            except OSError:
                pass

    # Register cleanup on graceful shutdown
    atexit.register(_cleanup_mp_dir)

    log.info(
        "Prometheus multiprocess dir: %s (%d workers, %s storage)",
        mp_dir,
        settings.UVICORN_WORKERS,
        "file-backed" if os.path.isdir(mp_dir) else "in-memory",
    )


def _cleanup_mp_dir():
    if os.path.isdir(mp_dir):
        try:
            shutil.rmtree(mp_dir, ignore_errors=True)
        except Exception:
            pass


def generate_metrics() -> bytes:
    """Generate aggregated metrics across all workers."""
    if os.path.isdir(mp_dir):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return generate_latest(registry)
    return generate_latest()


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        ACTIVE_REQUESTS.labels(method=method).inc()
        start = time.monotonic()
        try:
            response = await call_next(request)
            status = response.status_code
            REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(time.monotonic() - start)
            return response
        except Exception:
            REQUEST_COUNT.labels(method=method, endpoint=path, status=500).inc()
            raise
        finally:
            ACTIVE_REQUESTS.labels(method=method).dec()
