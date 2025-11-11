from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse

from .routers import requests as requests_router_module
from ..core.errors import DomainError, to_http_exception

# Application metadata and OpenAPI configuration
openapi_tags = [
    {
        "name": "Health",
        "description": "Service health and diagnostics endpoints.",
    },
    {
        "name": "Requests",
        "description": "Create and manage customer service requests and their status/history.",
    },
]

app = FastAPI(
    title="Customer Service Portal API",
    description=(
        "Backend API for managing customer service requests, enabling users to submit "
        "inquiries, update status, and view request history."
    ),
    version="0.1.0",
    openapi_tags=openapi_tags,
)

# CORS configuration (kept permissive for scaffolding; tighten later as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# PUBLIC_INTERFACE
@app.get(
    "/",
    tags=["Health"],
    summary="Health Check",
    operation_id="health_check",
    responses={
        200: {
            "description": "Healthy response payload",
            "content": {"application/json": {"schema": {"type": "object", "properties": {"message": {"type": "string"}}}}},
        }
    },
)
def health_check():
    """
    Returns a simple healthy message to confirm the service is running.

    Returns:
        dict: A JSON payload with a 'message' key set to 'Healthy'.
    """
    return {"message": "Healthy"}


# Domain error handler -> HTTPException mapping for a consistent payload
@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError):
    http_exc = to_http_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code or 500,
        content={"detail": http_exc.detail if http_exc.detail else "Error"},
    )


# Create an APIRouter for future app-level routes if needed
api_router = APIRouter()


# PUBLIC_INTERFACE
@api_router.get(
    "/docs/help",
    tags=["Health"],
    summary="API Documentation Help",
    operation_id="api_docs_help",
    responses={
        200: {
            "description": "Documentation help payload",
            "content": {"application/json": {"schema": {"type": "object"}}},
        }
    },
)
def docs_help():
    """
    Provide pointers to the interactive API docs and the OpenAPI specification.

    Notes:
    - The FastAPI runtime-generated OpenAPI spec at /openapi.json is authoritative.
    - Interactive Swagger UI is available at /docs and ReDoc at /redoc.
    - There are currently no WebSocket endpoints in this service; all routes are REST.
    - Tags are organized as:
        - Health: service diagnostics
        - Requests: create and manage customer service requests
    Returns:
        dict: A JSON payload with locations of API docs and spec.
    """
    return {
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi_json": "/openapi.json",
        "note": "Runtime-generated /openapi.json is authoritative for this service.",
        "websocket": "No WebSocket endpoints are defined in this service.",
    }


# Include the Requests router with a /requests prefix
api_router.include_router(
    requests_router_module.router,
    prefix="/requests",
    tags=["Requests"],
)

# Mount application routers
app.include_router(api_router)
