import logging
import json
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        req_id = request_id_var.get()
        if req_id:
            log_data["request_id"] = req_id

        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_data, ensure_ascii=False)


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        request_id_var.set(req_id)

        logger = logging.getLogger("diagram2algo.http")
        start = time.perf_counter()

        logger.info(
            "request_start",
            extra={"method": request.method, "path": request.url.path},
        )

        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "request_end | %s %s | %d | %.0fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        from app.routes.metrics import inc_counter, observe_histogram
        inc_counter("http_requests_total")
        observe_histogram("http_request_duration_ms", duration_ms)
        if response.status_code >= 400:
            inc_counter("http_errors_total")

        response.headers["X-Request-ID"] = req_id
        return response


def setup_logging(json_format: bool = False, level: str = "INFO"):
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))

    root.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
