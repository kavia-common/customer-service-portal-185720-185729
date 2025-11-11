from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

from .routers import requests as requests_router_module

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


@app.get("/", tags=["Health"], summary="Health Check")
def health_check():
    """
    PUBLIC_INTERFACE
    Returns a simple healthy message to confirm the service is running.

    Returns:
        dict: A JSON payload with a 'message' key set to 'Healthy'.
    """
    return {"message": "Healthy"}


# Create an APIRouter for future app-level routes if needed
api_router = APIRouter()

# Include the Requests router with a /requests prefix
api_router.include_router(
    requests_router_module.router,
    prefix="/requests",
    tags=["Requests"],
)

# Mount application routers
app.include_router(api_router)
