import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from app.logging_config import request_id_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, header: str = "X-Request-ID"):
        super().__init__(app)
        self.header = header

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get(self.header) or str(uuid.uuid4())
        request.state.request_id = req_id
        token = request_id_var.set(req_id)
        try:
            response = await call_next(request)
            response.headers[self.header] = req_id
            return response
        finally:
            request_id_var.reset(token)
