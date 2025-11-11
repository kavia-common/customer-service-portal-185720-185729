from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Optional, Tuple

from .schemas import AttachmentMeta
from .errors import NotFoundError, RepositoryError


ATTACHMENTS_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..",
    "..",
    "attachments",
)

# Ensure path resolves to project-level attachments dir
ATTACHMENTS_BASE_DIR = os.path.abspath(ATTACHMENTS_BASE_DIR)


@dataclass
class _AttachmentEntity:
    id: str
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    file_path: str


class AttachmentStore:
    """
    Process-local attachment store that persists files to a temp folder within the project
    and keeps metadata in-memory, associated to a request id.

    This is NOT durable beyond process lifecycle; suitable for tests and local dev only.
    """

    # Defaults: 10 MB per file, simple allowlist by prefix groups
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024
    DEFAULT_ALLOWED_MIME_PREFIXES = ("image/", "text/", "application/pdf")

    def __init__(
        self,
        base_dir: Optional[str] = None,
        max_bytes: int = DEFAULT_MAX_BYTES,
        allowed_mime_prefixes: Tuple[str, ...] = DEFAULT_ALLOWED_MIME_PREFIXES,
    ) -> None:
        self.base_dir = base_dir or ATTACHMENTS_BASE_DIR
        self.max_bytes = max_bytes
        self.allowed_mime_prefixes = allowed_mime_prefixes
        self._lock = RLock()
        self._by_request: Dict[str, List[_AttachmentEntity]] = {}
        os.makedirs(self.base_dir, exist_ok=True)

    def _ensure_request_dir(self, request_id: str) -> str:
        req_dir = os.path.join(self.base_dir, request_id)
        os.makedirs(req_dir, exist_ok=True)
        return req_dir

    def _to_meta(self, ent: _AttachmentEntity) -> AttachmentMeta:
        return AttachmentMeta(
            id=ent.id,
            filename=ent.filename,
            content_type=ent.content_type,
            size_bytes=ent.size_bytes,
            uploaded_at=ent.uploaded_at,
        )

    # PUBLIC_INTERFACE
    def add(
        self,
        request_id: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> AttachmentMeta:
        """
        Store file content on disk and index metadata in memory.

        Raises:
            RepositoryError: for storage issues.
            ValueError: for validation failures.
        """
        if not filename or filename.strip() == "":
            raise ValueError("filename is required")

        size = len(data)
        if size <= 0:
            raise ValueError("Empty file is not allowed")
        if size > self.max_bytes:
            raise ValueError(f"File too large (max {self.max_bytes} bytes)")

        # Validate content type: basic allowlist
        if not content_type:
            raise ValueError("content_type is required")
        if not any(content_type.startswith(p) for p in self.allowed_mime_prefixes):
            raise ValueError("Unsupported content type")

        # Persist to disk
        att_id = str(uuid.uuid4())
        uploaded_at = datetime.now(tz=timezone.utc)
        req_dir = self._ensure_request_dir(request_id)
        # Use constant-time file naming to avoid collisions
        safe_name = os.path.basename(filename)
        target = os.path.join(req_dir, f"{att_id}__{safe_name}")
        try:
            with open(target, "wb") as f:
                f.write(data)
        except OSError as e:
            raise RepositoryError(f"Failed to store attachment: {e}") from e

        ent = _AttachmentEntity(
            id=att_id,
            filename=safe_name,
            content_type=content_type,
            size_bytes=size,
            uploaded_at=uploaded_at,
            file_path=target,
        )

        with self._lock:
            self._by_request.setdefault(request_id, []).append(ent)

        return self._to_meta(ent)

    # PUBLIC_INTERFACE
    def list(self, request_id: str) -> List[AttachmentMeta]:
        """Return list of attachment metadata for a request."""
        with self._lock:
            ents = list(self._by_request.get(request_id, []))
        return [self._to_meta(e) for e in ents]

    # PUBLIC_INTERFACE
    def get_file(self, request_id: str, attachment_id: str) -> Tuple[str, _AttachmentEntity]:
        """
        Return (filepath, entity) for the given request and attachment id.

        Raises:
            NotFoundError: if not found.
        """
        with self._lock:
            ents = self._by_request.get(request_id, [])
            for e in ents:
                if e.id == attachment_id:
                    if not os.path.isfile(e.file_path):
                        raise NotFoundError("Attachment content missing")
                    return e.file_path, e
        raise NotFoundError(f"Attachment {attachment_id} not found for request {request_id}")
