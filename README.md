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

Additional rules:
- When closing a request (… -> closed) or reopening (resolved/closed -> in_progress), a non-empty note is required.

## Endpoints overview

Health and docs:
- GET /
  - Returns {"message": "Healthy"} for simple health checks.
- GET /docs/help
  - Returns pointers to Swagger UI (/docs), ReDoc (/redoc), and the OpenAPI JSON (/openapi.json).

Requests:
- POST /requests
  - Create a new service request (initial status = "new").
  - Requires Authorization: Bearer <CSP_API_TOKEN> (falls back to dev token if not set).
- GET /requests/{id}
  - Retrieve a service request by ID.
- PATCH /requests/{id}/status
  - Update the status of a service request (enforces workflow).
  - Requires Authorization: Bearer <CSP_API_TOKEN> (falls back to dev token if not set).
- GET /requests
  - List service requests with optional filters (status, q, customer_id, created_from, created_to) and pagination (page, page_size).
- GET /requests/{id}/history
  - Retrieve the chronological status update history for a request.
- POST /requests/{id}/attachments
  - Multipart upload (field "file"). Stores file on disk under ./attachments/{id}/ with in-memory metadata.
  - Requires Authorization: Bearer <CSP_API_TOKEN> (falls back to dev token if not set).
- GET /requests/{id}/attachments
  - List attachment metadata for a request.
- GET /requests/{id}/attachments/{attachment_id}
  - Download attachment content (streams file). Returns correct content type and filename.

For precise request/response schemas and examples, refer to the live OpenAPI at /openapi.json or the interactive docs.

## Request and response models (summary)

- ServiceRequestCreate
  - title (string, required; 3-120), description (string 1-5000 if provided), customer_id (optional; ^[A-Za-z0-9_-]{3,64}$)
- StatusUpdateCreate
  - status (enum: new | in_progress | resolved | closed, required), note (string 1-2000 if provided; required when closing/reopening)
- ServiceRequestOut / ServiceRequestListItem
  - id, title, description, status, created_at, updated_at, customer_id (optional)
- ServiceRequestListResponse
  - items (list of ServiceRequestListItem), total, page, page_size
- ServiceRequestHistoryResponse
  - id, history (list of { status, note, at })

## Validation, filters, and pagination

- Pagination uses page (>=1) and page_size (1..100).
- Filters:
  - status: One of new, in_progress, resolved, closed.
  - q: Free-text search in title and description (1-256 chars if provided).
  - customer_id: Optional, pattern ^[A-Za-z0-9_-]{3,64}$.
  - created_from / created_to: Date-only (YYYY-MM-DD), inclusive. If created_to is earlier than created_from, a 422 validation error is returned.
- Results are ordered by created_at descending.

## Standardized error responses

All errors follow a consistent JSON envelope:
```json
{
  "error": {
    "code": "string_identifier",
    "message": "Human-readable message",
    "details": {}
  }
}
```

Common codes:
- validation_error (422)
- not_found (404)
- invalid_transition (409)
- repository_error (500)
- internal_error (500)

## Persistence and repository abstraction

- This implementation uses an in-memory, process-local, thread-safe repository (RLock) for simplicity and speed during development and testing.
- The business logic (RequestService) depends on an abstract Repository interface defined in src/core/repository.py. This allows swapping the in-memory repository with a database-backed implementation in the future (e.g., SQL or NoSQL) without changing route handlers or service logic.
- Tests override the RequestService dependency to ensure test isolation with a fresh repository per test.

## Authentication

Write operations require a static Bearer token.
- Set environment variable CSP_API_TOKEN to your desired token value before starting the server.
- If not set, a development fallback token 'dev-token-CHANGE-ME' is accepted.
- Send header: Authorization: Bearer <token>

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
- Attachments are stored under ./attachments in the repo root with metadata kept in-memory; all data is ephemeral and cleared when the process restarts. Defaults: 10MB max per file; allowed content types: image/*, text/*, application/pdf.
- CORS is permissive for development; tighten configuration before production.