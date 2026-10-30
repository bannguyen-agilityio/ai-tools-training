"""The single error envelope (spec 6.1).

Shape: {"error": {"code", "message", "details": [{"field", "issue"}], "stack"}}.
`details` only on validation failures. `stack` only on unhandled errors and never when
ENVIRONMENT=production. Messages never echo submitted values.
"""

import logging
import traceback
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings

log = logging.getLogger("app.errors")

STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    503: "SERVICE_UNAVAILABLE",
}


class ProblemError(Exception):
    """Raise to return the error envelope. `detail` is the user-facing message."""

    def __init__(self, status: int, detail: str | None = None, code: str | None = None) -> None:
        super().__init__(detail or HTTPStatus(status).phrase)
        self.status = status
        self.detail = detail
        self.code = code  # stable UPPER_SNAKE reason, e.g. "NO_WORKING_DAYS"


def error_response(
    status: int,
    message: str | None = None,
    code: str | None = None,
    details: list[dict[str, str]] | None = None,
    stack: str | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {
        "code": code or STATUS_CODES.get(status, "INTERNAL_ERROR"),
        "message": message or HTTPStatus(status).phrase,
    }
    if details:
        error["details"] = details
    if stack is not None and get_settings().environment != "production":
        error["stack"] = stack
    return JSONResponse({"error": error}, status_code=status)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def _problem(_: Request, exc: ProblemError) -> JSONResponse:
        return error_response(exc.status, exc.detail, exc.code)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Field locations and messages only: never echo submitted values.
        errors = exc.errors()
        details = [{"field": ".".join(str(p) for p in e["loc"]), "issue": e["msg"]} for e in errors]
        # Unknown fields are a malformed request (400); any other rule failure is a 422.
        unknown_only = bool(errors) and all(e["type"] == "extra_forbidden" for e in errors)
        return error_response(
            400 if unknown_only else 422,
            "Request validation failed.",
            "VALIDATION_ERROR",
            details,
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Log the type only: exception text and tracebacks can carry request data.
        log.error(
            "unhandled error %s on %s %s", type(exc).__name__, request.method, request.url.path
        )
        stack = "".join(traceback.format_exception(exc))
        return error_response(500, code="INTERNAL_ERROR", stack=stack)
