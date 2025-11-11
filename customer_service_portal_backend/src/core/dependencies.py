from __future__ import annotations

from typing import Generator

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



