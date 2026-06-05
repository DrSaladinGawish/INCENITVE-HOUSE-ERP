import json
import logging
import logging.handlers
import os
from contextvars import ContextVar
from datetime import datetime, timezone

from app.config import settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            payload["exception"] = self.formatException(record.exc_info)
        if record.request_id:
            payload["request_id"] = record.request_id
        return json.dumps(payload, default=str)


def setup_logging() -> logging.Logger:
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    for h in root.handlers[:]:
        root.removeHandler(h)

    rid_filter = RequestIDFilter()

    console = logging.StreamHandler()
    console.setFormatter(JSONFormatter())
    console.addFilter(rid_filter)
    root.addHandler(console)

    log_dir = os.path.join(os.path.dirname(settings.ARCHIVE_ROOT), "logs") if settings.ARCHIVE_ROOT else "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "ihe-erp.log")
    rotator = logging.handlers.RotatingFileHandler(log_path, maxBytes=10 * 1024 * 1024, backupCount=5)
    rotator.setFormatter(JSONFormatter())
    rotator.addFilter(rid_filter)
    root.addHandler(rotator)

    return logging.getLogger(settings.APP_NAME)
