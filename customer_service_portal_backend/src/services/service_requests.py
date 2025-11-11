from __future__ import annotations

from typing import Optional, Tuple

from ..core.errors import NotFoundError, ValidationError
from ..models import (
    RequestEventRead,
    RequestStatus,
    ServiceRequestCreate,
    ServiceRequestListFilters,
    ServiceRequestRead,
    ServiceRequestUpdateStatus,
)
from ..persistence.repository import Repository


class ServiceRequestService:
    """
    Service layer implementing business logic for Service Requests.

    Responsibilities:
      - Validate cross-field business rules beyond schema validation.
      - Map repository None/False returns into domain errors.
      - Provide a stable API for the API layer to consume.
    """

    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    # PUBLIC_INTERFACE
    def create(self, payload: ServiceRequestCreate) -> ServiceRequestRead:
        """
        Create a new service request after applying domain validations.

        Raises:
          ValidationError: if domain-level constraints are violated.
        """
        # Domain rule example: subject should not duplicate description entirely
        if payload.subject.strip() == payload.description.strip():
            raise ValidationError("subject must not be identical to description", code="SUBJECT_EQUALS_DESCRIPTION")

        return self._repo.create_request(payload)

    # PUBLIC_INTERFACE
    def get(self, request_id: int) -> ServiceRequestRead:
        """
        Retrieve a service request by id.

        Raises:
          NotFoundError: if the request does not exist.
        """
        item = self._repo.get_request_by_id(request_id)
        if item is None:
            raise NotFoundError(f"Service request {request_id} not found", code="REQUEST_NOT_FOUND")
        return item

    # PUBLIC_INTERFACE
    def list(self, filters: Optional[ServiceRequestListFilters] = None) -> Tuple[int, list[ServiceRequestRead]]:
        """
        List service requests per provided filters and pagination.
        """
        return self._repo.list_requests(filters)

    # PUBLIC_INTERFACE
    def update_status(self, request_id: int, payload: ServiceRequestUpdateStatus) -> ServiceRequestRead:
        """
        Update the status of a request and append an event.

        Raises:
          NotFoundError: if the request does not exist.
          ValidationError: if transition is invalid.
        """
        # Example validation: CLOSED can only follow RESOLVED
        if payload.status == RequestStatus.CLOSED:
            # Ensure current state is RESOLVED
            existing = self._repo.get_request_by_id(request_id)
            if existing is None:
                raise NotFoundError(f"Service request {request_id} not found", code="REQUEST_NOT_FOUND")
            if existing.status != RequestStatus.RESOLVED:
                raise ValidationError(
                    "Cannot close a request that is not RESOLVED",
                    code="INVALID_STATUS_TRANSITION",
                    details={"from": existing.status.value, "to": payload.status.value},
                )

        updated = self._repo.update_status(
            request_id=request_id,
            status=payload.status,
            comment=payload.comment,
            updated_by=payload.updated_by,
        )
        if updated is None:
            raise NotFoundError(f"Service request {request_id} not found", code="REQUEST_NOT_FOUND")
        return updated

    # PUBLIC_INTERFACE
    def history(self, request_id: int) -> list[RequestEventRead]:
        """
        Return the history (events) for a given service request.

        Raises:
          NotFoundError: if the request does not exist.
        """
        # Ensure the request exists to return 404 for unknown IDs
        _ = self._repo.get_request_by_id(request_id)
        if _ is None:
            raise NotFoundError(f"Service request {request_id} not found", code="REQUEST_NOT_FOUND")
        return self._repo.list_events_for_request(request_id)
