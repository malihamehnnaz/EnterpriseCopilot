import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import reset_request_id, set_request_id

logger = logging.getLogger("app.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adds request correlation IDs and structured access logging."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        token = set_request_id(request_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "request.completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.url.query),
                    "client": request.client.host if request.client else "unknown",
                    "duration_ms": elapsed_ms,
                },
            )
            reset_request_id(token)

        response.headers["x-request-id"] = request_id
        return response