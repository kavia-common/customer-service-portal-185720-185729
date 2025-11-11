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
    responses={
        201: {"description": "Service request created"},
        400: {"description": "Validation error"},
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
    responses={
        200: {"description": "Service request found"},
        404: {"description": "Service request not found"},
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
    responses={
        200: {"description": "Status updated"},
        400: {"description": "Invalid status transition"},
        404: {"description": "Service request not found"},
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
    summary="List service requests",
    description=(
        "List service requests with optional filtering and pagination. "
        "Results are ordered by created_at descending."
    ),
    responses={
        200: {"description": "List of service requests"},
    },
)
async def list_requests(
    status: Optional[StatusEnum] = Query(None, description="Optional status filter"),
    q: Optional[str] = Query(None, description="Optional free-text search (title/description)"),
    customer_id: Optional[str] = Query(None, description="Filter by customer id"),
    created_from: Optional[date] = Query(None, description="Include requests created on/after this date (YYYY-MM-DD)"),
    created_to: Optional[date] = Query(None, description="Include requests created on/before this date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    svc: RequestService = Depends(get_service),
) -> ServiceRequestListResponse:
    """
    List service requests with filters and pagination.
    """
    # Input validation: ensure created_to not before created_from
    if created_from and created_to and created_to < created_from:
        # Consistent with FastAPI validation error shape for clarity
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="created_to must be on or after created_from")

    try:
        items, total = svc.list(
            status=status,
            q=q,
            page=page,
            page_size=page_size,
            customer_id=customer_id,
            created_from=created_from,
            created_to=created_to,
        )
        return ServiceRequestListResponse(
            items=items, total=total, page=page, page_size=page_size
        )
    except DomainError as e:
        raise to_http_exception(e) from e


# PUBLIC_INTERFACE
@router.get(
    "/{id}/history",
    response_model=ServiceRequestHistoryResponse,
    summary="Get the status change history for a service request",
    description="Retrieve the chronological history of status updates for a given request.",
    responses={
        200: {"description": "History retrieved"},
        404: {"description": "Service request not found"},
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
