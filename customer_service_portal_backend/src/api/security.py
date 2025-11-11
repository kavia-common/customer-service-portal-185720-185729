import os
from typing import Optional

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from starlette import status as http_status

# PUBLIC_INTERFACE
class AuthConfig:
    """Holds authentication configuration sourced from environment."""

    def __init__(self) -> None:
        # Prefer environment variable CSP_API_TOKEN; if not set, fall back to a dev token.
        # This is intentionally simple static-token auth for write operations.
        self.expected_token: str = os.getenv("CSP_API_TOKEN", "dev-token-CHANGE-ME")
        self.scheme_name: str = "BearerAuth"


_security_scheme = HTTPBearer(auto_error=False)


def _error_envelope(code: str, message: str, details: Optional[dict] = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


# PUBLIC_INTERFACE
async def require_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_security_scheme),
    config: AuthConfig = Depends(AuthConfig),
):
    """FastAPI dependency that enforces a static Bearer token for protected endpoints.

    Behavior:
    - If Authorization header is missing or malformed -> 401 with standardized error.
    - If token doesn't match configured static token -> 403 with standardized error.
    - On success, returns True (no user context for simplicity).
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        # 401 Unauthorized when no/malformed credentials
        return JSONResponse(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            content=_error_envelope(
                "unauthorized",
                "Missing or invalid Authorization header. Expected: Bearer <token>",
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.credentials != config.expected_token:
        # 403 Forbidden when credentials provided but invalid
        return JSONResponse(
            status_code=http_status.HTTP_403_FORBIDDEN,
            content=_error_envelope(
                "forbidden",
                "Invalid credentials for requested operation",
            ),
        )
    return True
