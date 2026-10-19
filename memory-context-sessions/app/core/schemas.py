"""Shared response schemas for the standard error envelope."""

from pydantic import BaseModel


class ValidationErrorDetail(BaseModel):
    """A single field-level validation error."""

    field: str
    message: str
    type: str


class ErrorBody(BaseModel):
    """Inner body of the standard error envelope."""

    code: str
    message: str
    details: list[ValidationErrorDetail] | None = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all endpoints on failure."""

    error: ErrorBody
