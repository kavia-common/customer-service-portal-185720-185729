from __future__ import annotations

from typing import Generator, Optional

from fastapi import Header

from ..persistence import get_repository
from ..persistence.repository import Repository, SupportsClose


# PUBLIC_INTERFACE
def get_repo() -> Generator[Repository, None, None]:
    """
    FastAPI dependency to provide a repository instance.

    Yields the current Repository implementation selected by configuration.
    Ensures proper closure if the repository supports explicit close/teardown.
    """
    repo = get_repository()
    try:
        yield repo
    finally:
        if isinstance(repo, SupportsClose):
            try:
                repo.close()
            except Exception:
                # Best-effort close; avoid raising during dependency teardown
                pass


# PUBLIC_INTERFACE
def get_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    """
    Dependency to read an optional API key from 'X-API-Key' header.

    This is currently permissive and returns an empty string if not provided.
    Future hardening can enforce presence and verification against configuration.
    """
    # For future use: enforce expected key from env if required.
    return x_api_key or ""
