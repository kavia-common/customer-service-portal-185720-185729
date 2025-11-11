# customer-service-portal-185720-185729

Customer Service Portal - Backend (FastAPI)

This backend exposes REST endpoints for creating and managing customer service requests.

API metadata:
- Title: Customer Service Portal API
- Version: 0.1.0

Entities:
- ServiceRequest
  - id, title, description, status, created_at, updated_at
- StatusUpdate (history entry)
  - status, note, at (timestamp)

Status workflow:
- new -> in_progress -> resolved | closed
- resolved -> in_progress (reopen)
- closed -> in_progress (reopen)
- Idempotent updates are allowed (setting the same status again).

Implemented endpoints:
- POST /requests
  - Create a new service request (initial status = "new")
- GET /requests/{id}
  - Retrieve a service request by ID
- PATCH /requests/{id}/status
  - Update the status of a service request (enforces workflow)
- GET /requests
  - List service requests with optional filters (status, q) and pagination (page, page_size)
- GET /requests/{id}/history
  - Retrieve the chronological status update history for a request

Health endpoint:
- GET /
  - Returns {"message": "Healthy"}

Run the API locally:
- Using uvicorn (dev): uvicorn customer_service_portal_backend.src.api.main:app --reload --port 3001

Notes:
- Data persistence is in-memory and process-local, implemented via a thread-safe repository (RLock).
- The runtime /openapi.json served by the FastAPI app is the source of truth.
- The static interfaces/openapi.json file is a stub.