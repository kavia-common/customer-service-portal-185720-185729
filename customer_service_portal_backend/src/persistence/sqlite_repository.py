from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Optional, Tuple

from ..models import (
    RequestEventRead,
    RequestStatus,
    ServiceRequestCreate,
    ServiceRequestListFilters,
    ServiceRequestRead,
)
from .repository import Repository


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS service_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS request_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    FOREIGN KEY(request_id) REFERENCES service_requests(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_requests_status ON service_requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_priority ON service_requests(priority);
CREATE INDEX IF NOT EXISTS idx_requests_email ON service_requests(customer_email);
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON service_requests(created_at);

CREATE INDEX IF NOT EXISTS idx_events_request_id ON request_events(request_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON request_events(created_at);
"""


class SQLiteRepository(Repository):
    """
    SQLite-backed repository using Python's standard sqlite3 library.

    - Initializes schema at startup.
    - Stores timestamps as ISO8601 strings (UTC naive) for portability.
    """

    def __init__(self, database_url: str) -> None:
        # sqlite3.connect accepts filenames; if database_url is a full URL, allow file: or :memory:
        self._db_url = database_url or ":memory:"
        self._conn = sqlite3.connect(self._db_url, check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.executescript(SCHEMA_SQL)

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    # PUBLIC_INTERFACE
    def create_request(self, payload: ServiceRequestCreate) -> ServiceRequestRead:
        now = datetime.utcnow().isoformat()
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO service_requests(subject, description, customer_email, status, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.subject,
                    payload.description,
                    str(payload.customer_email),
                    RequestStatus.NEW.value,
                    payload.priority.value,
                    now,
                    now,
                ),
            )
            rid = cur.lastrowid
            # initial event
            cur.execute(
                """
                INSERT INTO request_events(request_id, status, comment, created_at, created_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (rid, RequestStatus.NEW.value, "Request created", now, str(payload.customer_email)),
            )
            return self._fetch_request_by_id(cur, rid)  # type: ignore[return-value]

    # PUBLIC_INTERFACE
    def get_request_by_id(self, request_id: int) -> Optional[ServiceRequestRead]:
        with self._cursor() as cur:
            return self._fetch_request_by_id(cur, request_id)

    # PUBLIC_INTERFACE
    def list_requests(
        self, filters: Optional[ServiceRequestListFilters] = None
    ) -> Tuple[int, list[ServiceRequestRead]]:
        base = "FROM service_requests WHERE 1=1"
        params: list[object] = []

        if filters and filters.status is not None:
            base += " AND status = ?"
            params.append(filters.status.value)
        if filters and filters.priority is not None:
            base += " AND priority = ?"
            params.append(filters.priority.value)
        if filters and filters.customer_email is not None:
            base += " AND customer_email = ?"
            params.append(str(filters.customer_email))
        if filters and filters.date_from is not None:
            df = (
                filters.date_from.isoformat()  # type: ignore[attr-defined]
                if hasattr(filters.date_from, "isoformat")
                else datetime.combine(filters.date_from, datetime.min.time()).isoformat()  # type: ignore[arg-type]
            )
            base += " AND created_at >= ?"
            params.append(df)
        if filters and filters.date_to is not None:
            dt = (
                filters.date_to.isoformat()  # type: ignore[attr-defined]
                if hasattr(filters.date_to, "isoformat")
                else datetime.combine(filters.date_to, datetime.max.time()).isoformat()  # type: ignore[arg-type]
            )
            base += " AND created_at <= ?"
            params.append(dt)

        limit = (filters.limit if filters else 20)
        offset = (filters.offset if filters else 0)

        # total
        with self._cursor() as cur:
            cur.execute(f"SELECT COUNT(*) {base}", params)
            total = int(cur.fetchone()[0])  # type: ignore[index]

            # page
            cur.execute(
                f"""
                SELECT id, subject, description, customer_email, status, priority, created_at, updated_at
                {base}
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            )
            rows = cur.fetchall()
            items = [self._row_to_read(row) for row in rows]
            return total, items

    # PUBLIC_INTERFACE
    def add_event(
        self, request_id: int, status: RequestStatus, comment: str, created_by: str
    ) -> Optional[RequestEventRead]:
        now = datetime.utcnow().isoformat()
        with self._cursor() as cur:
            # ensure request exists
            cur.execute("SELECT 1 FROM service_requests WHERE id = ?", (request_id,))
            if cur.fetchone() is None:
                return None
            cur.execute(
                """
                INSERT INTO request_events(request_id, status, comment, created_at, created_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_id, status.value, comment, now, created_by),
            )
            evt_id = cur.lastrowid
            cur.execute(
                "SELECT id, request_id, status, comment, created_at, created_by FROM request_events WHERE id = ?",
                (evt_id,),
            )
            row = cur.fetchone()
            return self._event_row_to_read(row) if row else None

    # PUBLIC_INTERFACE
    def list_events_for_request(self, request_id: int) -> list[RequestEventRead]:
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT id, request_id, status, comment, created_at, created_by
                FROM request_events
                WHERE request_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (request_id,),
            )
            rows = cur.fetchall()
            return [self._event_row_to_read(r) for r in rows]

    # PUBLIC_INTERFACE
    def update_status(
        self, request_id: int, status: RequestStatus, comment: Optional[str], updated_by: str
    ) -> Optional[ServiceRequestRead]:
        now = datetime.utcnow().isoformat()
        with self._cursor() as cur:
            cur.execute("SELECT 1 FROM service_requests WHERE id = ?", (request_id,))
            if cur.fetchone() is None:
                return None
            cur.execute(
                "UPDATE service_requests SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, now, request_id),
            )
            cur.execute(
                """
                INSERT INTO request_events(request_id, status, comment, created_at, created_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_id, status.value, (comment or ""), now, updated_by),
            )
            return self._fetch_request_by_id(cur, request_id)

    # PUBLIC_INTERFACE
    def delete_request(self, request_id: int) -> bool:
        with self._cursor() as cur:
            cur.execute("DELETE FROM service_requests WHERE id = ?", (request_id,))
            return cur.rowcount > 0

    def _fetch_request_by_id(self, cur: sqlite3.Cursor, request_id: int) -> Optional[ServiceRequestRead]:
        cur.execute(
            """
            SELECT id, subject, description, customer_email, status, priority, created_at, updated_at
            FROM service_requests WHERE id = ?
            """,
            (request_id,),
        )
        row = cur.fetchone()
        return self._row_to_read(row) if row else None

    def _row_to_read(self, row: tuple) -> ServiceRequestRead:
        return ServiceRequestRead(
            id=row[0],
            subject=row[1],
            description=row[2],
            customer_email=row[3],
            status=RequestStatus(row[4]),
            priority=row[5],  # Pydantic will coerce to Priority enum
            created_at=datetime.fromisoformat(row[6]),
            updated_at=datetime.fromisoformat(row[7]),
        )

    def _event_row_to_read(self, row: tuple) -> RequestEventRead:
        return RequestEventRead(
            id=row[0],
            request_id=row[1],
            status=RequestStatus(row[2]),
            comment=row[3],
            created_at=datetime.fromisoformat(row[4]),
            created_by=row[5],
        )
