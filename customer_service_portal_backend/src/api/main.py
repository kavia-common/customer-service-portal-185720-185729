from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.config import get_settings
from ..persistence import get_repository

settings = get_settings()
app = FastAPI(
    title="Customer Service Portal Backend",
    description="Handles business logic and API endpoints for customer service management.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Health Check", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    # Touch the repository to ensure it initializes correctly on startup
    _ = get_repository()
    return {"message": "Healthy"}
