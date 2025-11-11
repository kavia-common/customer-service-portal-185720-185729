from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Header
from starlette import status

from .config import get_settings
from .errors import DomainError, _error_response


@dataclass(frozen=True)
class Principal:
    """
    Represents the authenticated principal identity and role.
    role can be 'customer' or 'staff'.
    """
    role: str
    api_key: str


class AuthError(DomainError):
    """
    Authentication/Authorization error with HTTP mapping.
    """

    def __init__(self, message: str, *, code: Optional[str] = None, http_status: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(message, code=code)
        self.http_status = http_status


def auth_exception_response(exc: AuthError):
    """
    Convert an AuthError to a structured JSONResponse, keeping consistent schema.
    """
    # reuse internal helper to standardize shape
    return _error_response(
        http_status=exc.http_status,
        err_type="auth_error" if exc.http_status == status.HTTP_401_UNAUTHORIZED else "forbidden",
        message=exc.message,
        code=exc.code,
        details=None,
    )


# PUBLIC_INTERFACE
async def get_principal(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> Optional[Principal]:
    """
    Resolve the authenticated principal from the X-API-Key header.

    Behavior:
      - If AUTH_ENABLED=false (default), returns None (no auth).
      - If AUTH_ENABLED=true and header missing/invalid -> raises AuthError 401.
      - If key matches STAFF_API_KEY -> Principal(role='staff').
      - Else if key matches CUSTOMER_API_KEY -> Principal(role='customer').
      - Else -> raises AuthError 401.
    """
    settings = get_settings()

    if not settings.AUTH_ENABLED:
        # Auth is disabled; treat as open access. Return None principal.
        return None

    # When enabled, key must be provided
    if not x_api_key:
        raise AuthError("Missing API key", code="MISSING_API_KEY", http_status=status.HTTP_401_UNAUTHORIZED)

    # Validate staff first (most privileged)
    if settings.STAFF_API_KEY and x_api_key == settings.STAFF_API_KEY:
        return Principal(role="staff", api_key=x_api_key)

    # Validate customer key next
    if settings.CUSTOMER_API_KEY and x_api_key == settings.CUSTOMER_API_KEY:
        return Principal(role="customer", api_key=x_api_key)

    # Unknown key
    raise AuthError("Invalid API key", code="INVALID_API_KEY", http_status=status.HTTP_401_UNAUTHORIZED)


# PUBLIC_INTERFACE
def require_customer(principal: Optional[Principal]) -> None:
    """
    Enforce that the caller is an authenticated 'customer' when auth is enabled.

    If AUTH_ENABLED=false, this is a no-op.
    If enabled and role is not 'customer', raise 403.
    """
    settings = get_settings()
    if not settings.AUTH_ENABLED:
        return
    if principal is None or principal.role != "customer":
        raise AuthError("Customer API key required", code="FORBIDDEN_CUSTOMER_ONLY", http_status=status.HTTP_403_FORBIDDEN)


# PUBLIC_INTERFACE
def require_staff(principal: Optional[Principal]) -> None:
    """
    Enforce that the caller is an authenticated 'staff' when auth is enabled.

    If AUTH_ENABLED=false, this is a no-op.
    If enabled and role is not 'staff', raise 403.
    """
    settings = get_settings()
    if not settings.AUTH_ENABLED:
        return
    if principal is None or principal.role != "staff":
        raise AuthError("Staff API key required", code="FORBIDDEN_STAFF_ONLY", http_status=status.HTTP_403_FORBIDDEN)
