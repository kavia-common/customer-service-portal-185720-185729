from typing import Optional
from datetime import date

from fastapi import APIRouter, Path, Query, status, Depends

from ...core.schemas import (
    ServiceRequestCreate,
    StatusUpdateCreate,
    ServiceRequestOut,
    ServiceRequestListResponse,
    ServiceRequestHistoryResponse,
    StatusEnum,
    ListRequestFilters,
    ErrorResponse,
)
from ...core.errors import DomainError, to_http_exception
from ...core.repository import InMemoryRepository
from ...core.services import RequestService

router = APIRouter()


def get_service() -> RequestService:
    """
    Dependency provider for RequestService.
    Uses a module-level singleton repository to persist data during process lifetime.
    """
    # Singleton in-memory repo for the app process
    global _repo_singleton
    try:
        _repo_singleton  # type: ignore[name-defined]
    except NameError:
        _repo_singleton = InMemoryRepository()  # type: ignore[assignment]
    return RequestService(_repo_singleton)  # type: ignore[name-defined]


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=ServiceRequestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service request",
    description="Create a new customer service request.",
    operation_id="create_request",
    responses={
        201: {
            "description": "Service request created",
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ServiceRequestOut"}}},
        },
        422: {
            "description": "Validation error",
            "model": ErrorResponse,
        },
        500: {"description": "Internal error", "model": ErrorResponse},
    },
)
async def create_request(
    payload: ServiceRequestCreate, svc: RequestService = Depends(get_service)
) -> ServiceRequestOut:
    """
    Create a service request.

    Args:
        payload (ServiceRequestCreate): The payload containing request details.

    Returns:
        ServiceRequestOut: The created request.
    """
    try:
        return svc.create(payload)
    except DomainError as e:
        raise to_http_exception(e) from e


# PUBLIC_INTERFACE
@router.get(
    "/{id}",
    response_model=ServiceRequestOut,
    summary="Get a service request by ID",
    description="Retrieve a single service request by its identifier.",
    operation_id="get_request_by_id",
    responses={
        200: {
            "description": "Service request found",
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ServiceRequestOut"}}},
        },
        404: {"description": "Service request not found", "model": ErrorResponse},
        500: {"description": "Internal error", "model": ErrorResponse},
    },
)
async def get_request(
    id: str = Path(..., description="The unique identifier of the service request"),
    svc: RequestService = Depends(get_service),
) -> ServiceRequestOut:
    """
    Retrieve a service request by ID.
    """
    try:
        return svc.get(id)
    except DomainError as e:
        raise to_http_exception(e) from e


# PUBLIC_INTERFACE
@router.patch(
    "/{id}/status",
    response_model=ServiceRequestOut,
    summary="Update the status of a service request",
    description="Update the status of an existing service request and return the updated entity.",
    operation_id="update_request_status",
    responses={
        200: {
            "description": "Status updated",
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ServiceRequestOut"}}},
        },
        404: {"description": "Service request not found", "model": ErrorResponse},
        409: {"description": "Invalid status transition", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        500: {"description": "Internal error", "model": ErrorResponse},
    },
)
async def update_request_status(
    payload: StatusUpdateCreate,
    id: str = Path(..., description="The unique identifier of the service request"),
    svc: RequestService = Depends(get_service),
) -> ServiceRequestOut:
    """
    Update a service request's status.
    """
    try:
        return svc.update_status(id, payload.status, payload.note)
    except DomainError as e:
        raise to_http_exception(e) from e


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=ServiceRequestListResponse,
    summary="List service requests (supports search with 'q')",
    description=(
        "List service requests with optional filtering and pagination. "
        "Supports case-insensitive substring search across title and description via the 'q' parameter. "
        "Results are ordered by created_at descending."
    ),
    operation_id="list_requests",
    responses={
        200: {
            "description": "List of service requests",
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ServiceRequestListResponse"}}},
        },
        422: {"description": "Validation error", "model": ErrorResponse},
        500: {"description": "Internal error", "model": ErrorResponse},
    },
)
async def list_requests(
    status: Optional[StatusEnum] = Query(None, description="Optional status filter"),
    q: Optional[str] = Query(
        None,
        description="Optional case-insensitive substring search across title and description",
    ),
    customer_id: Optional[str] = Query(None, description="Filter by customer id"),
    created_from: Optional[date] = Query(None, description="Include requests created on/after this date (YYYY-MM-DD)"),
    created_to: Optional[date] = Query(None, description="Include requests created on/before this date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    svc: RequestService = Depends(get_service),
) -> ServiceRequestListResponse:
    """
    List service requests with filters and pagination.

    Parameters:
        status: Optional status filter.
        q: Optional free-text search in title/description.
        customer_id: Filter by customer id.
        created_from: Include requests created on/after this date (YYYY-MM-DD).
        created_to: Include requests created on/before this date (YYYY-MM-DD).
        page: Page number (1-indexed).
        page_size: Page size (1-100).
    Returns:
        ServiceRequestListResponse: Items and pagination metadata.
    """
    # Delegate validation to Pydantic model so OpenAPI reflects constraints
    filters = ListRequestFilters(
        status=status,
        q=q,
        customer_id=customer_id,
        created_from=created_from,
        created_to=created_to,
        page=page,
        page_size=page_size,
    )

    items, total = svc.list(
        status=filters.status,
        q=filters.q,
        page=filters.page,
        page_size=filters.page_size,
        customer_id=filters.customer_id,
        created_from=filters.created_from,
        created_to=filters.created_to,
    )
    return ServiceRequestListResponse(items=items, total=total, page=filters.page, page_size=filters.page_size)


# PUBLIC_INTERFACE
@router.get(
    "/{id}/history",
    response_model=ServiceRequestHistoryResponse,
    summary="Get the status change history for a service request",
    description="Retrieve the chronological history of status updates for a given request.",
    operation_id="get_request_history",
    responses={
        200: {
            "description": "History retrieved",
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ServiceRequestHistoryResponse"}}},
        },
        404: {"description": "Service request not found", "model": ErrorResponse},
        500: {"description": "Internal error", "model": ErrorResponse},
    },
)
async def get_request_history(
    id: str = Path(..., description="The unique identifier of the service request"),
    svc: RequestService = Depends(get_service),
) -> ServiceRequestHistoryResponse:
    """
    Get a service request's history.
    """
    try:
        return svc.history(id)
    except DomainError as e:
        raise to_http_exception(e) from e
