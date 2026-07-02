import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from app.config import settings

log = logging.getLogger(__name__)
_limiter = None


def setup_rate_limiter(app, requests_per_minute=100):
    global _limiter
    workers = max(settings.UVICORN_WORKERS, 1)

    if settings.REDIS_URL:
        storage = settings.REDIS_URL
        limit = f"{requests_per_minute}/minute"
        log.info("Rate limiter using Redis (%s) — %s per client", storage, limit)
    else:
        per_process = max(requests_per_minute // workers, 1)
        storage = "memory://"
        limit = f"{per_process}/minute"
        log.warning(
            "No REDIS_URL configured. Rate limiter using per-process memory storage "
            "with %s workers — effective ceiling is %s/min (target: %s/min). "
            "Set REDIS_URL for accurate shared rate limiting.",
            workers, per_process * workers, requests_per_minute,
        )

    _limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[limit],
        storage_uri=storage,
    )
    app.state.limiter = _limiter
    app.add_middleware(SlowAPIMiddleware)


def get_limiter():
    return _limiter
