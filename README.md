# customer-service-portal-185720-185729

## Authentication

Lightweight API key authentication is available and controlled via environment variables:

- AUTH_ENABLED: enable API key auth when set to true/1/yes/on. Default: disabled.
- CUSTOMER_API_KEY: key required for customers to create requests (POST /requests) when auth is enabled.
- STAFF_API_KEY: key required for staff operations including listing, reading, status updates, history, and deletion.

Header: set X-API-Key with the appropriate key.

Error responses (401/403) follow a structured schema:
{
  "error": {
    "type": "auth_error" | "forbidden",
    "message": "...",
    "code": "MISSING_API_KEY" | "INVALID_API_KEY" | "FORBIDDEN_CUSTOMER_ONLY" | "FORBIDDEN_STAFF_ONLY"
  }
}