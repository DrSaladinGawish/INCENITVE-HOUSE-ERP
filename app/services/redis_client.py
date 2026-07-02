import json
import logging
from datetime import timedelta
from typing import Any, Callable, Optional

from app.config import settings

log = logging.getLogger(__name__)

_redis = None
_pool = None


async def init_redis():
    global _redis, _pool
    if not settings.REDIS_URL:
        log.info("REDIS_URL not set — Redis caching disabled")
        return
    try:
        import redis.asyncio as aioredis

        _pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=True,
        )
        _redis = aioredis.Redis(connection_pool=_pool)
        await _redis.ping()
        log.info("Redis connected: %s", settings.REDIS_URL)
    except Exception:
        log.warning("Redis connection failed — caching falls back to in-process")
        _redis = None
        _pool = None


async def close_redis():
    global _redis, _pool
    if _redis:
        await _redis.aclose()
        _redis = None
    if _pool:
        await _pool.disconnect()
        _pool = None
    log.info("Redis connection closed")


def get_redis():
    return _redis


async def set_cache(key: str, value: Any, ttl: int = 30):
    r = _redis
    if r is None:
        return
    try:
        serialized = json.dumps(value, default=str)
        await r.setex(key, timedelta(seconds=ttl), serialized)
    except Exception:
        log.warning("Redis set failed for key: %s", key)


async def get_cache(key: str) -> Optional[Any]:
    r = _redis
    if r is None:
        return None
    try:
        raw = await r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        log.warning("Redis get failed for key: %s", key)
        return None


async def delete_cache(key: str):
    r = _redis
    if r is None:
        return
    try:
        await r.delete(key)
    except Exception:
        log.warning("Redis delete failed for key: %s", key)


def cached(cache_key_prefix: str, ttl: int = 30):
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            from app.services.redis_client import get_cache, set_cache

            key = f"{cache_key_prefix}:{hash((args, tuple(sorted(kwargs.items()))))}"
            cached_val = await get_cache(key)
            if cached_val is not None:
                return cached_val
            result = await func(*args, **kwargs)
            await set_cache(key, result, ttl=ttl)
            return result

        return wrapper

    return decorator
