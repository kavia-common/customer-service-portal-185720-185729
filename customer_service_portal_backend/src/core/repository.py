from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .schemas import (
    ServiceRequestCreate,
    ServiceRequestOut,
    ServiceRequestListItem,
    StatusEnum,
    StatusUpdateOut,
)


@dataclass
class _ServiceRequestEntity:
    """Internal storage model for a service request (in-memory only)."""
    id: str
    title: str
    description: Optional[str]
    status: StatusEnum
    created_at: datetime
    updated_at: datetime
    customer_id: Optional[str] = None
    history: List[StatusUpdateOut] = field(default_factory=list)


# PUBLIC_INTERFACE
class Repository:
    """Abstract repository interface for service requests."""

    def create_request(self, payload: ServiceRequestCreate) -> ServiceRequestOut:
        """Create a service request."""
        raise NotImplementedError

    def get_request(self, request_id: str) -> Optional[ServiceRequestOut]:
        """Get a service request by ID."""
        raise NotImplementedError

    def update_status(
        self, request_id: str, status: StatusEnum, note: Optional[str]
    ) -> Optional[ServiceRequestOut]:
        """Update status and append a history entry if the entity exists."""
        raise NotImplementedError

    def list_requests(
        self,
        status: Optional[StatusEnum],
        q: Optional[str],
        page: int,
        page_size: int,
        customer_id: Optional[str] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
    ) -> Tuple[List[ServiceRequestListItem], int]:
        """List requests with filtering and pagination. Returns (items, total)."""
        raise NotImplementedError

    def get_history(self, request_id: str) -> Optional[List[StatusUpdateOut]]:
        """Return the chronological history of a request or None if not found."""
        raise NotImplementedError


# PUBLIC_INTERFACE
class InMemoryRepository(Repository):
    """
    Thread-safe in-memory repository.

    Uses an RLock to allow re-entrant access from the same thread if needed.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: Dict[str, _ServiceRequestEntity] = {}

    def create_request(self, payload: ServiceRequestCreate) -> ServiceRequestOut:
        now = datetime.utcnow()
        with self._lock:
            request_id = str(uuid.uuid4())
            entity = _ServiceRequestEntity(
                id=request_id,
                title=payload.title,
                description=payload.description,
                status=StatusEnum.new,
                created_at=now,
                updated_at=now,
                customer_id=payload.customer_id,
                history=[StatusUpdateOut(status=StatusEnum.new, note=None, at=now)],
            )
            self._store[request_id] = entity
            return self._to_out(entity)

    def get_request(self, request_id: str) -> Optional[ServiceRequestOut]:
        with self._lock:
            entity = self._store.get(request_id)
            return self._to_out(entity) if entity else None

    def update_status(
        self, request_id: str, status: StatusEnum, note: Optional[str]
    ) -> Optional[ServiceRequestOut]:
        now = datetime.utcnow()
        with self._lock:
            entity = self._store.get(request_id)
            if not entity:
                return None
            entity.status = status
            entity.updated_at = now
            entity.history.append(StatusUpdateOut(status=status, note=note, at=now))
            return self._to_out(entity)

    def list_requests(
        self,
        status: Optional[StatusEnum],
        q: Optional[str],
        page: int,
        page_size: int,
        customer_id: Optional[str] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
    ) -> Tuple[List[ServiceRequestListItem], int]:
        with self._lock:
            items = list(self._store.values())

            # Filter by status
            if status is not None:
                items = [e for e in items if e.status == status]

            # Simple text search in title/description
            if q:
                q_lower = q.lower()
                items = [
                    e
                    for e in items
                    if q_lower in e.title.lower()
                    or (e.description or "").lower().find(q_lower) != -1
                ]

            # Filter by customer_id
            if customer_id:
                items = [e for e in items if e.customer_id == customer_id]

            # Date range filter on created_at (inclusive)
            if created_from is not None:
                items = [e for e in items if e.created_at >= created_from]
            if created_to is not None:
                # inclusive to the end of the 'created_to' day if a date was given at midnight
                items = [e for e in items if e.created_at <= created_to]

            # Sort by created_at desc for deterministic order
            items.sort(key=lambda e: e.created_at, reverse=True)

            total = len(items)

            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            page_slice = items[start:end]

            # Map to list item representation for the list endpoint
            return [self._to_list_item(e) for e in page_slice], total

    def get_history(self, request_id: str) -> Optional[List[StatusUpdateOut]]:
        with self._lock:
            entity = self._store.get(request_id)
            if not entity:
                return None
            # Already chronological by append-time
            return list(entity.history)

    @staticmethod
    def _to_out(entity: _ServiceRequestEntity) -> ServiceRequestOut:
        return ServiceRequestOut(
            id=entity.id,
            title=entity.title,
            description=entity.description,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            customer_id=entity.customer_id,
        )

    @staticmethod
    def _to_list_item(entity: _ServiceRequestEntity) -> ServiceRequestListItem:
        """
        Convert internal entity to a ServiceRequestListItem.
        Currently mirrors _to_out, but kept separate to allow future divergence
        between detail and list views without affecting other code paths.
        """
        return ServiceRequestListItem(
            id=entity.id,
            title=entity.title,
            description=entity.description,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            customer_id=entity.customer_id,
        )
