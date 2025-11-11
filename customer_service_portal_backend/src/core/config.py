from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv

# Load .env if present
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.

    Variables:
      - USE_SQLITE: "true"/"false" to force SQLite usage (default: false)
      - DATABASE_URL: SQLite file path or special values like ":memory:" (default unset)
      - PAGINATION_DEFAULT_LIMIT: int default for list endpoints (default: 20)
      - MAX_LIMIT: int maximum allowed page size (default: 100)
      - CORS_ORIGINS: comma-separated list of allowed origins (default: *)
      - AUTH_ENABLED: enable API key auth for requests (default: false)
      - CUSTOMER_API_KEY: API key for customer actions (POST create)
      - STAFF_API_KEY: API key for staff actions (list/get/history/update/delete)
    """

    def __init__(self) -> None:
        use_sqlite_raw = os.getenv("USE_SQLITE", "").strip().lower()
        self.USE_SQLITE: bool = use_sqlite_raw in ("1", "true", "yes", "on")
        self.DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL") or None
        self.PAGINATION_DEFAULT_LIMIT: int = int(os.getenv("PAGINATION_DEFAULT_LIMIT", "20"))
        self.MAX_LIMIT: int = int(os.getenv("MAX_LIMIT", "100"))

        cors_raw = os.getenv("CORS_ORIGINS", "*")
        if cors_raw.strip() == "*":
            self.CORS_ORIGINS: List[str] = ["*"]
        else:
            self.CORS_ORIGINS = [o.strip() for o in cors_raw.split(",") if o.strip()]

        auth_enabled_raw = os.getenv("AUTH_ENABLED", "").strip().lower()
        self.AUTH_ENABLED: bool = auth_enabled_raw in ("1", "true", "yes", "on")
        # Keys are only used if AUTH_ENABLED is true
        self.CUSTOMER_API_KEY: Optional[str] = os.getenv("CUSTOMER_API_KEY") or None
        self.STAFF_API_KEY: Optional[str] = os.getenv("STAFF_API_KEY") or None


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings loaded from environment."""
    return Settings()
