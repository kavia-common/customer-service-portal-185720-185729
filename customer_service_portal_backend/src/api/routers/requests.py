from typing import Optional

from fastapi import APIRouter, Path, Query

from ...core.schemas import (
    ServiceRequestCreate,
    StatusUpdateCreate,
    ServiceRequestResponse,
    ServiceRequestListResponse,
    ServiceRequestHistoryResponse,
)

router = APIRouter()


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=ServiceRequestResponse,
    summary="Create a new service request",
    description=(
        "Create a new customer service request. This endpoint accepts minimal "
        "request details and returns a placeholder response until full implementation."
    ),
    responses={
        201: {"description": "Service request created"},
        400: {"description": "Validation error"},
    },
)
async def create_request(payload: ServiceRequestCreate) -> ServiceRequestResponse:
    """
    Create a service request.

    This is a scaffolding endpoint; business logic and persistence are not implemented yet.

    Args:
        payload (ServiceRequestCreate): The payload containing request details.

    Returns:
        ServiceRequestResponse: Placeholder response model.

    TODO:
        - Validate business rules
        - Persist to database
        - Emit domain event(s)
    """
    # Placeholder: raise to indicate not implemented in Step 1
    raise NotImplementedError("Create request is not implemented yet.")


# PUBLIC_INTERFACE
@router.get(
    "/{id}",
    response_model=ServiceRequestResponse,
    summary="Get a service request by ID",
    description="Retrieve a single service request by its identifier.",
    responses={
        200: {"description": "Service request found"},
        404: {"description": "Service request not found"},
    },
)
async def get_request(
    id: str = Path(..., description="The unique identifier of the service request"),
) -> ServiceRequestResponse:
    """
    Retrieve a service request by ID.

    Args:
        id (str): The request identifier.

    Returns:
        ServiceRequestResponse: Placeholder response model.

    TODO:
        - Fetch from datastore
        - Map persistence model to API schema
    """
    raise NotImplementedError("Get request by ID is not implemented yet.")


# PUBLIC_INTERFACE
@router.patch(
    "/{id}/status",
    response_model=ServiceRequestResponse,
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
) -> ServiceRequestResponse:
    """
    Update a service request's status.

    Args:
        id (str): The request identifier.
        payload (StatusUpdateCreate): The status update details.

    Returns:
        ServiceRequestResponse: Placeholder updated entity.

    TODO:
        - Validate transition rules
        - Persist status change and history entry
    """
    raise NotImplementedError("Update request status is not implemented yet.")


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=ServiceRequestListResponse,
    summary="List service requests",
    description=(
        "List service requests with simple filtering and pagination placeholders. "
        "Filtering/pagination will be implemented in a subsequent step."
    ),
    responses={
        200: {"description": "List of service requests"},
    },
)
async def list_requests(
    status: Optional[str] = Query(
        None, description="Optional status filter (placeholder)"
    ),
    q: Optional[str] = Query(
        None, description="Optional free-text search (placeholder)"
    ),
    page: int = Query(1, ge=1, description="Page number (placeholder)"),
    page_size: int = Query(20, ge=1, le=100, description="Page size (placeholder)"),
) -> ServiceRequestListResponse:
    """
    List service requests.

    Args:
        status (Optional[str]): Filter by status (placeholder).
        q (Optional[str]): Free-text search (placeholder).
        page (int): Page number (placeholder).
        page_size (int): Page size (placeholder).

    Returns:
        ServiceRequestListResponse: Placeholder collection response.

    TODO:
        - Implement filtering, sorting, pagination
        - Integrate with datastore
    """
    raise NotImplementedError("List requests is not implemented yet.")


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
) -> ServiceRequestHistoryResponse:
    """
    Get a service request's history.

    Args:
        id (str): The request identifier.

    Returns:
        ServiceRequestHistoryResponse: Placeholder history response model.

    TODO:
        - Retrieve and order history events
        - Consider pagination for long histories
    """
    raise NotImplementedError("Get request history is not implemented yet.")
