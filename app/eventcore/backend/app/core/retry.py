import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)


async def retry_async(func, *args, max_retries=3, delay=30.0, backoff=2.0, **kwargs):
    from sqlalchemy.ext.asyncio import AsyncSession
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < max_retries:
                # Rollback any stale session before retry to clear aborted transaction
                for arg in list(args) + list(kwargs.values()):
                    if isinstance(arg, AsyncSession):
                        try:
                            await arg.rollback()
                        except Exception:
                            pass
                wait = delay * (backoff ** (attempt - 1))
                logger.warning(
                    "Retry %d/%d for %s failed: %s. Waiting %.1fs...",
                    attempt, max_retries, func.__name__, e, wait,
                )
                await asyncio.sleep(wait)
    logger.error("All %d retries exhausted for %s: %s", max_retries, func.__name__, last_exc)
    raise last_exc


def with_retry(max_retries=3, delay=30.0, backoff=2.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, *args, max_retries=max_retries, delay=delay, backoff=backoff, **kwargs)
        return wrapper
    return decorator
