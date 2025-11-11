from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, status, Response

from ..core.dependencies import get_repo
from ..core.auth import get_principal, require_customer, require_staff, Principal
from ..models import (
    RequestEventRead,
    RequestStatus,
    ServiceRequestCreate,
    ServiceRequestListFilters,
    ServiceRequestRead,
    ServiceRequestUpdateStatus,
)
from ..persistence.repository import Repository
from ..services.service_requests import ServiceRequestService

router = APIRouter(
    prefix="/requests",
    tags=["Service Requests"],
)


def _service(repo: Repository) -> ServiceRequestService:
    """
    Internal helper to construct the service layer bound to a repository instance.
    """
    return ServiceRequestService(repo)


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=ServiceRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Service Request",
    description="Create a new service request. Initializes with status NEW and records an initial event.",
    responses={
        201: {"description": "Request created"},
        400: {"description": "Domain validation error"},
        422: {"description": "Input validation error or domain error"},
    },
)
def create_request(
    payload: ServiceRequestCreate,
    repo: Repository = Depends(get_repo),
    principal: Principal | None = Depends(get_principal),
) -> ServiceRequestRead:
    """
    Create a new service request.

    Parameters:
      - payload: ServiceRequestCreate body
    Returns:
      - ServiceRequestRead representing the created request
    """
    # Enforce customer role when auth is enabled
    require_customer(principal)

    svc = _service(repo)
    return svc.create(payload)


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=Dict[str, Any],
    summary="List Service Requests",
    description="List service requests with optional filters and pagination.",
    responses={
        200: {"description": "List of requests with pagination metadata"},
    },
)
def list_requests(
    status_filter: Optional[RequestStatus] = Query(default=None, alias="status", description="Filter by status"),
    priority: Optional[str] = Query(default=None, description="Filter by priority"),
    customer_email: Optional[str] = Query(default=None, description="Filter by customer email"),
    date_from: Optional[str] = Query(default=None, description="Include requests created on/after this ISO date/datetime"),
    date_to: Optional[str] = Query(default=None, description="Include requests created on/before this ISO date/datetime"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of items to return"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    repo: Repository = Depends(get_repo),
    principal: Principal | None = Depends(get_principal),
) -> Dict[str, Any]:
    """
    List service requests with filters/pagination.

    Query Parameters mirror ServiceRequestListFilters. Returns:
      - total: total count for the filter (unpaginated)
      - items: list of ServiceRequestRead
      - limit, offset: pagination echo
    """
    # Enforce staff role for listing when auth is enabled
    require_staff(principal)

    # Build a ServiceRequestListFilters instance. Pydantic will coerce where possible.
    filters = ServiceRequestListFilters(
        status=status_filter,
        priority=priority,  # Pydantic will coerce to Priority
        customer_email=customer_email,
        date_from=date_from,  # parsed by pydantic to date/datetime
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    svc = _service(repo)
    total, items = svc.list(filters)
    return {
        "total": total,
        "items": items,
        "limit": limit,
        "offset": offset,
    }


# PUBLIC_INTERFACE
@router.get(
    "/{request_id}",
    response_model=ServiceRequestRead,
    summary="Get Service Request by ID",
    description="Retrieve a single service request by its unique identifier.",
    responses={
        200: {"description": "Request found"},
        404: {"description": "Request not found"},
    },
)
def get_request_by_id(
    request_id: int = Path(..., ge=1, description="Service request ID"),
    repo: Repository = Depends(get_repo),
    principal: Principal | None = Depends(get_principal),
) -> ServiceRequestRead:
    """
    Get a service request by ID.

    Parameters:
      - request_id: integer ID path parameter
    Returns:
      - ServiceRequestRead
    """
    require_staff(principal)

    svc = _service(repo)
    return svc.get(request_id)


# PUBLIC_INTERFACE
@router.patch(
    "/{request_id}/status",
    response_model=ServiceRequestRead,
    summary="Update Service Request Status",
    description="Update the status of a service request and append an event to its history.",
    responses={
        200: {"description": "Status updated"},
        400: {"description": "Domain validation error"},
        404: {"description": "Request not found"},
    },
)
def update_request_status(
    request_id: int = Path(..., ge=1, description="Service request ID"),
    payload: ServiceRequestUpdateStatus = ...,
    repo: Repository = Depends(get_repo),
    principal: Principal | None = Depends(get_principal),
) -> ServiceRequestRead:
    """
    Update a service request's status and record an event.

    Parameters:
      - request_id: integer ID
      - payload: ServiceRequestUpdateStatus body
    Returns:
      - Updated ServiceRequestRead
    """
    require_staff(principal)

    svc = _service(repo)
    return svc.update_status(request_id, payload)


# PUBLIC_INTERFACE
@router.get(
    "/{request_id}/history",
    response_model=list[RequestEventRead],
    summary="Get Request History",
    description="Return chronological list of events for a service request.",
    responses={
        200: {"description": "History returned"},
        404: {"description": "Request not found"},
    },
)
def get_request_history(
    request_id: int = Path(..., ge=1, description="Service request ID"),
    repo: Repository = Depends(get_repo),
    principal: Principal | None = Depends(get_principal),
) -> list[RequestEventRead]:
    """
    Get events history for a service request.

    Parameters:
      - request_id: integer ID
    Returns:
      - List of RequestEventRead
    """
    require_staff(principal)

    svc = _service(repo)
    return svc.history(request_id)


# PUBLIC_INTERFACE
@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Service Request",
    description="Delete a service request and its events. No content returned if deletion succeeds.",
    responses={
        204: {"description": "Deleted"},
        404: {"description": "Request not found"},
    },
)
def delete_request(
    request_id: int = Path(..., ge=1, description="Service request ID"),
    repo: Repository = Depends(get_repo),
    principal: Principal | None = Depends(get_principal),
) -> Response:
    """
    Delete a service request.

    Parameters:
      - request_id: integer ID
    Returns:
      - No Content (204) with an empty body.
    """
    # Enforce staff role for destructive action
    require_staff(principal)

    # Use repository directly via service to keep consistency on NotFound handling
    svc = _service(repo)
    # Reuse get to raise NotFound for unknown IDs
    _ = svc.get(request_id)
    # Perform deletion
    deleted = repo.delete_request(request_id)
    # If a race condition causes not found, treat as 404
    if not deleted:
        from ..core.errors import NotFoundError

        raise NotFoundError(f"Service request {request_id} not found", code="REQUEST_NOT_FOUND")
    # Explicitly return an empty 204 response (no body)
    return Response(status_code=status.HTTP_204_NO_CONTENT, content=None)
