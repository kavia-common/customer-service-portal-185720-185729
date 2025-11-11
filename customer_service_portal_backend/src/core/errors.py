from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status


class DomainError(Exception):
    """
    Base class for domain-specific errors within the application.

    Attributes:
      message: Human-readable error message.
      code: Optional machine-readable error code string.
      details: Optional dictionary with additional error context.
    """

    def __init__(self, message: str, *, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class NotFoundError(DomainError):
    """
    Raised when a requested resource could not be found.
    """


class ValidationError(DomainError):
    """
    Raised when a domain-level validation fails (not Pydantic input validation).
    """


class ConflictError(DomainError):
    """
    Raised when an operation conflicts with the current state of the resource.
    """


def _error_response(
    *, http_status: int, err_type: str, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    payload = {
        "error": {
            "type": err_type,
            "message": message,
        }
    }
    if code:
        payload["error"]["code"] = code
    if details:
        payload["error"]["details"] = details
    return JSONResponse(status_code=http_status, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register FastAPI exception handlers for domain errors.

    This wires our DomainError hierarchy to structured JSON error responses so
    that downstream API layers return consistent error payloads.
    """

    @app.exception_handler(NotFoundError)
    async def _handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:  # pragma: no cover - FastAPI glue
        return _error_response(
            http_status=status.HTTP_404_NOT_FOUND,
            err_type="not_found",
            message=exc.message,
            code=exc.code,
            details=exc.details,
        )

    @app.exception_handler(ValidationError)
    async def _handle_validation(_: Request, exc: ValidationError) -> JSONResponse:  # pragma: no cover - FastAPI glue
        return _error_response(
            http_status=status.HTTP_400_BAD_REQUEST,
            err_type="validation_error",
            message=exc.message,
            code=exc.code,
            details=exc.details,
        )

    @app.exception_handler(ConflictError)
    async def _handle_conflict(_: Request, exc: ConflictError) -> JSONResponse:  # pragma: no cover - FastAPI glue
        return _error_response(
            http_status=status.HTTP_409_CONFLICT,
            err_type="conflict",
            message=exc.message,
            code=exc.code,
            details=exc.details,
        )

    @app.exception_handler(DomainError)
    async def _handle_domain(_: Request, exc: DomainError) -> JSONResponse:  # pragma: no cover - FastAPI glue
        return _error_response(
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            err_type="domain_error",
            message=exc.message,
            code=exc.code,
            details=exc.details,
        )
