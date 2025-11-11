from __future__ import annotations

from typing import List, Optional, Tuple
from datetime import datetime, date

from .errors import (
    NotFoundError,
    InvalidTransitionError,
)
from .repository import Repository
from .schemas import (
    ServiceRequestCreate,
    ServiceRequestOut,
    ServiceRequestListItem,
    ServiceRequestHistoryResponse,
    ServiceRequestHistoryEntry,
    StatusEnum,
)


# PUBLIC_INTERFACE
class RequestService:
    """
    Encapsulates business logic for service requests, including status transitions
    and history recording.
    """

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    # PUBLIC_INTERFACE
    def create(self, payload: ServiceRequestCreate) -> ServiceRequestOut:
        """Create a new request with initial status 'new' and a history entry."""
        return self.repo.create_request(payload)

    # PUBLIC_INTERFACE
    def get(self, request_id: str) -> ServiceRequestOut:
        """Retrieve an existing request or raise NotFoundError."""
        req = self.repo.get_request(request_id)
        if not req:
            raise NotFoundError(f"Request {request_id} not found")
        return req

    # PUBLIC_INTERFACE
    def list(
        self,
        status: Optional[StatusEnum],
        q: Optional[str],
        page: int,
        page_size: int,
        customer_id: Optional[str] = None,
        created_from: Optional[date] = None,
        created_to: Optional[date] = None,
    ) -> Tuple[List[ServiceRequestListItem], int]:
        """List requests supporting filters and pagination."""
        # Convert date-only to datetime range endpoints (UTC at start/end of day).
        dt_from: Optional[datetime] = (
            datetime.combine(created_from, datetime.min.time()) if created_from else None
        )
        dt_to: Optional[datetime] = (
            datetime.combine(created_to, datetime.max.time()) if created_to else None
        )
        return self.repo.list_requests(
            status=status,
            q=q,
            page=page,
            page_size=page_size,
            customer_id=customer_id,
            created_from=dt_from,
            created_to=dt_to,
        )

    # PUBLIC_INTERFACE
    def update_status(
        self, request_id: str, new_status: StatusEnum, note: Optional[str]
    ) -> ServiceRequestOut:
        """
        Update status enforcing allowed transitions and append a history entry.

        Allowed transitions:
        - new -> in_progress
        - in_progress -> resolved | closed
        - resolved -> in_progress (reopen)
        - closed -> in_progress (reopen)

        Additional rules:
        - When transitioning to 'closed' or reopening from 'resolved'/'closed' to 'in_progress',
          a non-empty note is required.
        """
        existing = self.repo.get_request(request_id)
        if not existing:
            raise NotFoundError(f"Request {request_id} not found")

        if not self._is_valid_transition(existing.status, new_status):
            raise InvalidTransitionError(
                f"Invalid status transition: {existing.status} -> {new_status}"
            )

        # Enforce note requirement for specific transitions
        if new_status == StatusEnum.closed and (note is None or not note.strip()):
            raise InvalidTransitionError("Closing a request requires a non-empty note")
        if (
            existing.status in (StatusEnum.resolved, StatusEnum.closed)
            and new_status == StatusEnum.in_progress
            and (note is None or not note.strip())
        ):
            raise InvalidTransitionError("Reopening a request requires a non-empty note")

        updated = self.repo.update_status(request_id, new_status, note)
        # repo.update_status returns None only if not found (we already checked)
        return updated  # type: ignore[return-value]

    # PUBLIC_INTERFACE
    def history(self, request_id: str) -> ServiceRequestHistoryResponse:
        """Return the chronological history for the request or NotFoundError."""
        req = self.repo.get_request(request_id)
        if not req:
            raise NotFoundError(f"Request {request_id} not found")

        hist = self.repo.get_history(request_id)
        assert hist is not None
        entries = [
            ServiceRequestHistoryEntry(status=h.status, note=h.note, at=h.at) for h in hist
        ]
        return ServiceRequestHistoryResponse(id=request_id, history=entries)

    @staticmethod
    def _is_valid_transition(old: StatusEnum, new: StatusEnum) -> bool:
        if old == new:
            return True  # idempotent update allowed

        if old == StatusEnum.new:
            return new == StatusEnum.in_progress

        if old == StatusEnum.in_progress:
            return new in (StatusEnum.resolved, StatusEnum.closed)

        if old in (StatusEnum.resolved, StatusEnum.closed):
            # allow reopening to in_progress
            return new == StatusEnum.in_progress

        return False
