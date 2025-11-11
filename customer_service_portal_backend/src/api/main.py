from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import logging

from ..core.config import get_settings
from ..core.errors import register_exception_handlers
from ..core.auth import AuthError, auth_exception_response
from ..persistence import get_repository
from .requests import router as requests_router

# Configure logger
logger = logging.getLogger("uvicorn.error")

settings = get_settings()
app = FastAPI(
    title="Customer Service Portal Backend",
    description="Handles business logic and API endpoints for customer service management.",
    version="0.1.0",
    openapi_tags=[
        {"name": "Health", "description": "Service health and readiness"},
        {"name": "Service Requests", "description": "Operations for managing service requests"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that injects a unique request ID into each incoming request for correlation.
    The ID is available as request.state.request_id and echoed via 'X-Request-ID' header.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log unhandled errors with request id context
            logger.exception("Unhandled error for request_id=%s", request_id)
            raise exc
        response.headers["X-Request-ID"] = request_id
        return response


# Register middleware
app.add_middleware(RequestIDMiddleware)

# Register centralized exception handlers for domain errors
register_exception_handlers(app)

# Register auth error handler for unified 401/403 responses
@app.exception_handler(AuthError)
async def _handle_auth_error(_: Request, exc: AuthError):
    return auth_exception_response(exc)

# Include API routers
app.include_router(requests_router)


@app.get("/", summary="Health Check", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    # Touch the repository to ensure it initializes correctly on startup
    _ = get_repository()
    return {"message": "Healthy"}
