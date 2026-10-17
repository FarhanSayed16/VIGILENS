"""Domain exceptions and HTTP exception handlers."""

from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error mapped to an HTTP response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "app_error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(message, status_code=404, code="not_found", **kwargs)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", **kwargs: Any) -> None:
        super().__init__(message, status_code=409, code="conflict", **kwargs)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", **kwargs: Any) -> None:
        super().__init__(message, status_code=401, code="unauthorized", **kwargs)


class PayloadTooLargeError(AppError):
    def __init__(self, message: str = "Upload too large", **kwargs: Any) -> None:
        super().__init__(message, status_code=413, code="payload_too_large", **kwargs)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        # Scaffold: avoid leaking internals; log at call site later
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred.",
                "details": {"type": type(exc).__name__},
            },
        )
