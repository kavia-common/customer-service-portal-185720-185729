import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app and the router's dependency to override for isolation
from customer_service_portal_backend.src.api.main import app
from customer_service_portal_backend.src.api.routers import requests as requests_router
from customer_service_portal_backend.src.core.repository import InMemoryRepository
from customer_service_portal_backend.src.core.services import RequestService


@pytest.fixture()
def client():
    """
    Provide a TestClient with a fresh in-memory repository for each test.

    The application has a dependency provider get_service that holds a module-level
    singleton repository. We override that dependency here to return a RequestService
    backed by a new InMemoryRepository per test, ensuring isolation and determinism.
    """
    repo = InMemoryRepository()

    def _override_get_service():
        return RequestService(repo)

    # Apply the dependency override for this test's lifecycle
    app.dependency_overrides[requests_router.get_service] = _override_get_service
    with TestClient(app) as c:
        yield c
    # Cleanup override after test
    app.dependency_overrides.pop(requests_router.get_service, None)
