from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, Optional, Tuple

from ..models import (
    RequestEvent,
    RequestEventRead,
    RequestStatus,
    ServiceRequest,
    ServiceRequestCreate,
    ServiceRequestListFilters,
    ServiceRequestRead,
)
from .repository import Repository


class InMemoryRepository(Repository):
    """
    Thread-safe in-memory repository implementation using dictionaries.

    Notes:
      - IDs are auto-incremented per entity type.
      - Timestamps use UTC naive datetime from datetime.utcnow().
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._requests: Dict[int, ServiceRequest] = {}
        self._events: Dict[int, RequestEvent] = {}
        self._req_id_seq: int = 0
        self._evt_id_seq: int = 0

    def _next_request_id(self) -> int:
        with self._lock:
            self._req_id_seq += 1
            return self._req_id_seq

    def _next_event_id(self) -> int:
        with self._lock:
            self._evt_id_seq += 1
            return self._evt_id_seq

    # PUBLIC_INTERFACE
    def create_request(self, payload: ServiceRequestCreate) -> ServiceRequestRead:
        now = datetime.utcnow()
        with self._lock:
            rid = self._next_request_id()
            entity: ServiceRequest = {
                "id": rid,
                "subject": payload.subject,
                "description": payload.description,
                "customer_email": str(payload.customer_email),
                "status": RequestStatus.NEW,
                "priority": payload.priority,
                "created_at": now,
                "updated_at": now,
            }
            self._requests[rid] = entity
            # Also create initial event
            self._create_event_locked(
                request_id=rid,
                status=RequestStatus.NEW,
                comment="Request created",
                created_by=str(payload.customer_email),
                at=now,
            )
            return self._to_read(entity)

    # PUBLIC_INTERFACE
    def get_request_by_id(self, request_id: int) -> Optional[ServiceRequestRead]:
        with self._lock:
            entity = self._requests.get(request_id)
            return self._to_read(entity) if entity else None

    # PUBLIC_INTERFACE
    def list_requests(
        self, filters: Optional[ServiceRequestListFilters] = None
    ) -> Tuple[int, list[ServiceRequestRead]]:
        with self._lock:
            items = list(self._requests.values())

            # filtering
            if filters:
                if filters.status is not None:
                    items = [r for r in items if r["status"] == filters.status]
                if filters.priority is not None:
                    items = [r for r in items if r["priority"] == filters.priority]
                if filters.customer_email is not None:
                    ce = str(filters.customer_email)
                    items = [r for r in items if r["customer_email"] == ce]
                if filters.date_from is not None:
                    df = (
                        datetime.combine(filters.date_from, datetime.min.time())
                        if isinstance(filters.date_from, datetime) is False
                        else filters.date_from
                    )
                    items = [r for r in items if r["created_at"] >= df]  # type: ignore[arg-type]
                if filters.date_to is not None:
                    dt = (
                        datetime.combine(filters.date_to, datetime.max.time())
                        if isinstance(filters.date_to, datetime) is False
                        else filters.date_to
                    )
                    items = [r for r in items if r["created_at"] <= dt]  # type: ignore[arg-type]

                limit = filters.limit
                offset = filters.offset
            else:
                limit = 20
                offset = 0

            # sort by created_at desc, id desc for stability
            items.sort(key=lambda r: (r["created_at"], r["id"]), reverse=True)

            total = len(items)
            sliced = items[offset : offset + limit]
            return total, [self._to_read(r) for r in sliced]

    # PUBLIC_INTERFACE
    def add_event(
        self, request_id: int, status: RequestStatus, comment: str, created_by: str
    ) -> Optional[RequestEventRead]:
        with self._lock:
            if request_id not in self._requests:
                return None
            evt = self._create_event_locked(request_id, status, comment, created_by, datetime.utcnow())
            return self._event_to_read(evt)

    # PUBLIC_INTERFACE
    def list_events_for_request(self, request_id: int) -> list[RequestEventRead]:
        with self._lock:
            events = [e for e in self._events.values() if e["request_id"] == request_id]
            events.sort(key=lambda e: (e["created_at"], e["id"]))
            return [self._event_to_read(e) for e in events]

    # PUBLIC_INTERFACE
    def update_status(
        self, request_id: int, status: RequestStatus, comment: Optional[str], updated_by: str
    ) -> Optional[ServiceRequestRead]:
        with self._lock:
            entity = self._requests.get(request_id)
            if not entity:
                return None
            now = datetime.utcnow()
            entity["status"] = status
            entity["updated_at"] = now
            self._requests[request_id] = entity
            self._create_event_locked(
                request_id=request_id,
                status=status,
                comment=comment or "",
                created_by=updated_by,
                at=now,
            )
            return self._to_read(entity)

    # PUBLIC_INTERFACE
    def delete_request(self, request_id: int) -> bool:
        with self._lock:
            if request_id not in self._requests:
                return False
            del self._requests[request_id]
            # delete events
            to_del = [eid for eid, e in self._events.items() if e["request_id"] == request_id]
            for eid in to_del:
                del self._events[eid]
            return True

    def _to_read(self, entity: ServiceRequest) -> ServiceRequestRead:
        return ServiceRequestRead(
            id=entity["id"],
            subject=entity["subject"],
            description=entity["description"],
            customer_email=entity["customer_email"],
            status=entity["status"],
            priority=entity["priority"],
            created_at=entity["created_at"],
            updated_at=entity["updated_at"],
        )

    def _event_to_read(self, evt: RequestEvent) -> RequestEventRead:
        return RequestEventRead(
            id=evt["id"],
            request_id=evt["request_id"],
            status=evt["status"],
            comment=evt["comment"],
            created_at=evt["created_at"],
            created_by=evt["created_by"],
        )

    def _create_event_locked(
        self, request_id: int, status: RequestStatus, comment: str, created_by: str, at: datetime
    ) -> RequestEvent:
        eid = self._next_event_id()
        evt: RequestEvent = {
            "id": eid,
            "request_id": request_id,
            "status": status,
            "comment": comment,
            "created_at": at,
            "created_by": created_by,
        }
        self._events[eid] = evt
        return evt
