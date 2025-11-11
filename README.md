# customer-service-portal-185720-185729

Customer Service Portal - Backend (FastAPI)

This backend exposes REST endpoints for creating and managing customer service requests.

API metadata:
- Title: Customer Service Portal API
- Version: 0.1.0

Entities (scaffolding):
- ServiceRequest
  - id, title, description, status
  - TODO: requester info, timestamps, priority, category, assignee, attachments
- StatusUpdate
  - status, note
  - TODO: timestamp, actor, reason, metadata

Planned endpoints (Step 1 scaffolding created):
- POST /requests
  - Create a new service request
- GET /requests/{id}
  - Retrieve a service request by ID
- PATCH /requests/{id}/status
  - Update the status of a service request
- GET /requests
  - List service requests with optional filters and pagination placeholders
- GET /requests/{id}/history
  - Retrieve the chronological status update history for a request

Health endpoint:
- GET /
  - Returns {"message": "Healthy"}

OpenAPI note:
- The runtime /openapi.json served by the FastAPI app is the source of truth.
- The static interfaces/openapi.json file is a stub and will be aligned in Step 4.