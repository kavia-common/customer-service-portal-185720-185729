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
def to_http_exception(err: DomainError) -> HTTPException:
    """
    Map domain errors to HTTPException suitable for FastAPI responses.
    """
    if isinstance(err, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    if isinstance(err, InvalidTransitionError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error")
