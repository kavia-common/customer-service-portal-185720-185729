from fastapi.testclient import TestClient

# Import the FastAPI app
from customer_service_portal_backend.src.api.main import app


def test_app_starts_and_health_endpoint():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    # Expected shape from health_check
    assert body.get("message") == "Healthy"
