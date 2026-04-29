import logging
import sys
from contextvars import ContextVar

from app.core.config import get_settings

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestFormatter(logging.Formatter):
    """Injects request metadata into log records."""

    def format(self, record: logging.LogRecord) -> str:
        record.request_id = request_id_ctx.get("-")
        record.method = getattr(record, "method", "-")
        record.path = getattr(record, "path", "-")
        record.duration_ms = getattr(record, "duration_ms", "-")
        return super().format(record)


def set_request_id(request_id: str):
    return request_id_ctx.set(request_id)


def reset_request_id(token) -> None:
    request_id_ctx.reset(token)


def configure_logging() -> None:
    """Configure structured console logging for the API."""

    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        RequestFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | req=%(request_id)s | %(message)s | %(method)s %(path)s | %(duration_ms)sms"
        )
    )

    logging.basicConfig(
        level=level,
        handlers=[handler],
        force=True,
    )
