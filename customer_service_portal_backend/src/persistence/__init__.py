from __future__ import annotations

from functools import lru_cache
from typing import Optional

from ..core.config import get_settings
from .memory_repository import InMemoryRepository
from .repository import Repository
from .sqlite_repository import SQLiteRepository


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_repository() -> Repository:
    """
    Return the active repository instance based on environment configuration.

    Selection logic:
      - If USE_SQLITE=true OR DATABASE_URL is provided -> SQLiteRepository
      - Else -> InMemoryRepository
    """
    settings = get_settings()
    if settings.USE_SQLITE or (settings.DATABASE_URL is not None):
        db_url = settings.DATABASE_URL or ":memory:"
        return SQLiteRepository(database_url=db_url)
    return InMemoryRepository()
