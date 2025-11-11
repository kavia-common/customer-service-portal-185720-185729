from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Protocol, Tuple

from ..models import (
    RequestEventRead,
    RequestStatus,
    ServiceRequestCreate,
    ServiceRequestListFilters,
    ServiceRequestRead,
)


class SupportsClose(Protocol):
    """Protocol for repositories that support explicit close/teardown."""

    def close(self) -> None:  # pragma: no cover - simple protocol
        ...


class Repository(ABC):
    """
    Abstract repository interface for persistence operations over Service Requests
    and their associated events.
    """

    # PUBLIC_INTERFACE
    @abstractmethod
    def create_request(self, payload: ServiceRequestCreate) -> ServiceRequestRead:
        """
        Create a new service request with initial status NEW and timestamps.
        Returns the created request as a read schema.
        """
        raise NotImplementedError

    # PUBLIC_INTERFACE
    @abstractmethod
    def get_request_by_id(self, request_id: int) -> Optional[ServiceRequestRead]:
        """
        Retrieve a request by its identifier. Returns None if not found.
        """
        raise NotImplementedError

    # PUBLIC_INTERFACE
    @abstractmethod
    def list_requests(
        self,
        filters: Optional[ServiceRequestListFilters] = None,
    ) -> Tuple[int, list[ServiceRequestRead]]:
        """
        List requests matching optional filters with pagination.

        Returns:
          (total_count, items)
        where total_count is the number of records matching filters (ignoring pagination),
        and items is the paginated list for the requested limit/offset.
        """
        raise NotImplementedError

    # PUBLIC_INTERFACE
    @abstractmethod
    def add_event(
        self,
        request_id: int,
        status: RequestStatus,
        comment: str,
        created_by: str,
    ) -> Optional[RequestEventRead]:
        """
        Append an event to a given request. Returns the created event or None if request doesn't exist.
        """
        raise NotImplementedError

    # PUBLIC_INTERFACE
    @abstractmethod
    def list_events_for_request(self, request_id: int) -> list[RequestEventRead]:
        """
        List all events associated with a given request, ordered by created_at ascending.
        """
        raise NotImplementedError

    # PUBLIC_INTERFACE
    @abstractmethod
    def update_status(
        self, request_id: int, status: RequestStatus, comment: Optional[str], updated_by: str
    ) -> Optional[ServiceRequestRead]:
        """
        Update the status of a given request and add an event for the transition.
        Returns the updated request or None if request doesn't exist.
        """
        raise NotImplementedError

    # PUBLIC_INTERFACE
    @abstractmethod
    def delete_request(self, request_id: int) -> bool:
        """
        Delete a request and its events. Returns True if deletion occurred, False if not found.
        """
        raise NotImplementedError
