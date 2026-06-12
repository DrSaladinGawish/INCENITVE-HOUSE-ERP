"""Surgery v4.1 — Real dependency functions for dashboard endpoints."""

from typing import Optional
from fastapi import Header, HTTPException, Request
from app.core.security import decode_token
from app.core.cookie_auth import get_token_from_cookie


class AuthRequiredException(HTTPException):
    """Raised when auth is missing/invalid. Exception handler converts to redirect for HTML."""
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status_code=401, detail=detail)


async def get_current_user(
    request: Request = None,
    authorization: Optional[str] = Header(None),
):
    """Unified auth: Bearer header first, then httpOnly cookie fallback."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    elif request is not None:
        token = get_token_from_cookie(request)
    if not token:
        raise AuthRequiredException()
    payload = decode_token(token)
    if payload is None:
        raise AuthRequiredException("Invalid or expired token")
    return {"user_id": payload.get("sub"), "role": payload.get("role", "user")}


async def require_permission(user: dict, permission: str):
    """Stub: check user role/permission against a required permission string."""
    # TODO: lookup user.role in a permission table; raise HTTPException(403) if denied
    _ = permission  # no-op: accept all permissions in stub
    return True


async def get_redis():
    """Stub: return a Redis client for caching / rate-limiting."""
    # TODO: connect to redis via aioredis / redis-py; handle connection pool
    return None


async def log_audit_entry(user_id: str, action: str, entity_type: str, entity_id: str):
    """Stub: write an audit log row to the database."""
    # TODO: INSERT into audit_log table (user_id, action, entity_type, entity_id, timestamp)
    _ = user_id, action, entity_type, entity_id
    print(f"[AUDIT] {user_id} performed {action} on {entity_type}#{entity_id}")


async def generate_invoice_pdf(invoice_id: str) -> bytes:
    """Stub: generate a PDF invoice and return raw bytes."""
    # TODO: use ReportLab / WeasyPrint to build PDF from invoice data
    _ = invoice_id
    return b"%PDF-1.4 stub invoice content"


def validate_date_range(start_date: str, end_date: str):
    """Stub: validate ISO date string range (start <= end)."""
    # TODO: parse ISO dates, compare; raise HTTPException(422) on invalid range
    _ = start_date, end_date
    return True
