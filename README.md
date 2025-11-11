# customer-service-portal-185720-185729

Customer Service Portal - Backend (FastAPI)

This backend exposes REST endpoints for creating and managing customer service requests. It is designed with a repository abstraction so the current in-memory persistence layer can be swapped for a real database without changing the API surface.

## API metadata
- Title: Customer Service Portal API
- Version: 0.1.0

## How to run locally

Prerequisites:
- Python 3.11+
- Pip

Setup and run:
1. Change into the backend workspace folder:
   - cd customer-service-portal-185720-185729
2. Create and activate a virtual environment (recommended):
   - python -m venv .venv
   - source .venv/bin/activate  (Windows: .venv\Scripts\activate)
3. Install dependencies:
   - pip install -r customer_service_portal_backend/requirements.txt
4. Start the API server (development, with hot reload):
   - uvicorn customer_service_portal_backend.src.api.main:app --reload --port 3001

Once running, the service will be available at http://localhost:3001.

## Viewing API documentation

- Swagger UI: http://localhost:3001/docs
- ReDoc: http://localhost:3001/redoc
- OpenAPI JSON (authoritative): http://localhost:3001/openapi.json
- API docs helper: http://localhost:3001/docs/help

Note: A static OpenAPI stub exists at customer_service_portal_backend/interfaces/openapi.json, but the live runtime-generated /openapi.json is authoritative and always in sync with the code.

## Entities

- ServiceRequest
  - id, title, description, status, created_at, updated_at, customer_id (optional in this demo)
- StatusUpdate (history entry)
  - status, note, at (timestamp)

## Status workflow

Allowed transitions are enforced by business logic:
- new -> in_progress
- in_progress -> resolved | closed
- resolved -> in_progress (reopen)
- closed -> in_progress (reopen)
- Idempotent updates are allowed (setting the same status again).

## Endpoints overview

Health and docs:
- GET /
  - Returns {"message": "Healthy"} for simple health checks.
- GET /docs/help
  - Returns pointers to Swagger UI (/docs), ReDoc (/redoc), and the OpenAPI JSON (/openapi.json).

Requests:
- POST /requests
  - Create a new service request (initial status = "new").
- GET /requests/{id}
  - Retrieve a service request by ID.
- PATCH /requests/{id}/status
  - Update the status of a service request (enforces workflow).
- GET /requests
  - List service requests with optional filters (status, q, customer_id, created_from, created_to) and pagination (page, page_size).
- GET /requests/{id}/history
  - Retrieve the chronological status update history for a request.

For precise request/response schemas and examples, refer to the live OpenAPI at /openapi.json or the interactive docs.

## Request and response models (summary)

- ServiceRequestCreate
  - title (string, required), description (string, optional)
- StatusUpdateCreate
  - status (enum: new | in_progress | resolved | closed, required), note (string, optional)
- ServiceRequestOut / ServiceRequestListItem
  - id, title, description, status, created_at, updated_at, customer_id (optional)
- ServiceRequestListResponse
  - items (list of ServiceRequestListItem), total, page, page_size
- ServiceRequestHistoryResponse
  - id, history (list of { status, note, at })

## Sample cURL requests

Health:
```bash
curl -s http://localhost:3001/
```

Create a request:
```bash
curl -s -X POST "http://localhost:3001/requests" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Printer issue",
    "description": "Paper jam on floor 2"
  }'
```

Get a request by ID:
```bash
REQ_ID="replace-with-id"
curl -s "http://localhost:3001/requests/${REQ_ID}"
```

Update status (new -> in_progress):
```bash
REQ_ID="replace-with-id"
curl -s -X PATCH "http://localhost:3001/requests/${REQ_ID}/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "note": "Work started"
  }'
```

List requests (filters and pagination):
```bash
# All requests (default page=1, page_size=20)
curl -s "http://localhost:3001/requests"

# Search by text (title/description)
curl -s "http://localhost:3001/requests?q=printer"

# Filter by status
curl -s "http://localhost:3001/requests?status=in_progress"

# Date range (inclusive), format YYYY-MM-DD
curl -s "http://localhost:3001/requests?created_from=2025-01-01&created_to=2025-12-31"

# Pagination
curl -s "http://localhost:3001/requests?page=2&page_size=10"
```

Get status history:
```bash
REQ_ID="replace-with-id"
curl -s "http://localhost:3001/requests/${REQ_ID}/history"
```

## Validation, filters, and pagination

- Pagination uses page (>=1) and page_size (1..100).
- Filters:
  - status: One of new, in_progress, resolved, closed.
  - q: Free-text search in title and description.
  - customer_id: Optional field supported by the repository abstraction.
  - created_from / created_to: Date-only (YYYY-MM-DD), inclusive. If created_to is earlier than created_from, a 422 validation error is returned.
- Results are ordered by created_at descending.

## Persistence and repository abstraction

- This implementation uses an in-memory, process-local, thread-safe repository (RLock) for simplicity and speed during development and testing.
- The business logic (RequestService) depends on an abstract Repository interface defined in src/core/repository.py. This allows swapping the in-memory repository with a database-backed implementation in the future (e.g., SQL or NoSQL) without changing route handlers or service logic.
- Tests override the RequestService dependency to ensure test isolation with a fresh repository per test.

## Development notes

- Run tests:
  - cd customer-service-portal-185720-185729
  - pytest -q
- Linting:
  - flake8

## Project structure

- customer_service_portal_backend/src/api
  - main.py: App setup, health endpoints, router inclusion, CORS.
  - routers/requests.py: REST endpoints for service requests.
- customer_service_portal_backend/src/core
  - schemas.py: Pydantic models for request/response.
  - repository.py: Repository abstraction and in-memory implementation.
  - services.py: Business logic and status workflow enforcement.
  - errors.py: Domain errors and HTTP mapping.
- customer_service_portal_backend/interfaces/openapi.json: Static OpenAPI stub (may lag behind live spec).
- customer_service_portal_backend/tests: Pytest suite.

## Notes

- Data persistence is in-memory and process-local, implemented via a thread-safe repository (RLock).
- CORS is permissive for development; tighten configuration before production.