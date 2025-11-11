from __future__ import annotations

from fastapi import HTTPException, status


# PUBLIC_INTERFACE
class DomainError(Exception):
    """Base class for domain errors."""


# PUBLIC_INTERFACE
class NotFoundError(DomainError):
    """Raised when an entity cannot be located."""


# PUBLIC_INTERFACE
class InvalidTransitionError(DomainError):
    """Raised when a status transition violates business rules."""


# PUBLIC_INTERFACE
class RepositoryError(DomainError):
    """Raised when repository/persistence operations fail."""


# PUBLIC_INTERFACE
def to_http_exception(err: DomainError) -> HTTPException:
    """
    Map domain errors to HTTPException suitable for FastAPI responses.
    """
    if isinstance(err, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    if isinstance(err, InvalidTransitionError):
        # Map to 409 Conflict per requirement "invalid_transition"
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    if isinstance(err, RepositoryError):
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error")
