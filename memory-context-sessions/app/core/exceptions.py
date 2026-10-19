"""Application-level exception definitions.

Domain exceptions are independent of HTTP response formatting.
Exception handlers in ``app.core.error_handlers`` convert them
into the standard error envelope.
"""


class AppError(Exception):
    """Base exception for application errors.

    Every domain exception carries a ``code`` for programmatic handling,
    a ``message`` for human-readable context, and a ``status_code`` that
    the error handler maps to an HTTP status.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: list[dict[str, str]] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error description.
            code: Uppercase snake_case application error code.
            status_code: HTTP status code for the error response.
            details: Optional structured information about the error.
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AuthenticationError(AppError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "UNAUTHENTICATED",
    ) -> None:
        """Initialize the authentication error.

        Args:
            message: Human-readable error description.
            code: Uppercase snake_case application error code.
        """
        super().__init__(message=message, code=code, status_code=401)


class ConflictError(AppError):
    """Raised when an operation conflicts with existing state."""

    def __init__(
        self,
        message: str = "Resource already exists",
        code: str = "RESOURCE_CONFLICT",
    ) -> None:
        """Initialize the conflict error.

        Args:
            message: Human-readable error description.
            code: Uppercase snake_case application error code.
        """
        super().__init__(message=message, code=code, status_code=409)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "RESOURCE_NOT_FOUND",
    ) -> None:
        """Initialize the not-found error.

        Args:
            message: Human-readable error description.
            code: Uppercase snake_case application error code.
        """
        super().__init__(message=message, code=code, status_code=404)
