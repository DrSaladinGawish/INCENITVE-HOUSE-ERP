import asyncio
import time
from functools import wraps
from fastapi import HTTPException

_locks: dict[str, asyncio.Lock] = {}
_last_run: dict[str, float] = {}


def debounce(key_prefix: str, cooldown: float = 30.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            lock_key = f"{key_prefix}:lock"
            if lock_key not in _locks:
                _locks[lock_key] = asyncio.Lock()

            run_key = f"{key_prefix}:run"
            now = time.time()
            last = _last_run.get(run_key, 0)
            if now - last < cooldown:
                remaining = round(cooldown - (now - last), 1)
                raise HTTPException(
                    status_code=429,
                    detail=f"Operation '{key_prefix}' is on cooldown. "
                           f"Wait {remaining}s before retrying.",
                )

            async with _locks[lock_key]:
                cooldown_check = _last_run.get(run_key, 0)
                if now - cooldown_check < cooldown:
                    remaining = round(cooldown - (now - cooldown_check), 1)
                    raise HTTPException(
                        status_code=429,
                        detail=f"Operation '{key_prefix}' was just executed. "
                               f"Wait {remaining}s.",
                    )
                _last_run[run_key] = now
                return await func(*args, **kwargs)
        return wrapper
    return decorator
