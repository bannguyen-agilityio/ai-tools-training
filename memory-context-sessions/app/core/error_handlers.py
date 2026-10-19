"""Centralized exception handlers for the standard error envelope.

All handlers convert exceptions into a consistent JSON structure::

    {"error": {"code": "...", "message": "...", "details": ..., "request_id": ...}}
"""

import logging
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

_STATUS_TO_CODE: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "RESOURCE_NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "RESOURCE_CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _get_request_id(request: Request) -> str | None:
    """Return the request ID attached by middleware, if available."""
    return getattr(request.state, "request_id", None)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str | None,
    details: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build a ``JSONResponse`` following the standard error envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id,
            }
        },
        headers=headers,
    )


async def _app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert domain exceptions to the standard error envelope."""
    assert isinstance(exc, AppError)
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return _error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        request_id=_get_request_id(request),
        details=exc.details,
        headers=headers,
    )


async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Normalize Pydantic validation errors into the standard envelope."""
    assert isinstance(exc, RequestValidationError)
    details: list[dict[str, str]] = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            }
        )
    return _error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        request_id=_get_request_id(request),
        details=details,
    )


async def _http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Wrap Starlette/FastAPI HTTP exceptions in the standard envelope."""
    assert isinstance(exc, StarletteHTTPException)
    code = _STATUS_TO_CODE.get(exc.status_code, "UNKNOWN_ERROR")
    message = str(exc.detail) if exc.detail else "An error occurred."
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return _error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        request_id=_get_request_id(request),
        headers=headers,
    )


async def _unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Return a generic 500 for unexpected exceptions and log the details."""
    request_id = _get_request_id(request)
    logger.exception("Unhandled exception [request_id=%s]", request_id)
    return _error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred.",
        request_id=request_id,
    )


async def _request_id_middleware(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    """Attach a unique request ID to every incoming request."""
    request.state.request_id = f"req_{uuid.uuid4().hex[:12]}"
    return await call_next(request)


def register_error_handlers(app: FastAPI) -> None:
    """Register all exception handlers and the request-ID middleware.

    Args:
        app: The FastAPI application instance.
    """
    app.middleware("http")(_request_id_middleware)
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
