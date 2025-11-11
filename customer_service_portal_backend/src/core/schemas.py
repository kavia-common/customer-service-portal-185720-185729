from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Annotated
from pydantic import BaseModel, Field, field_validator, constr


# PUBLIC_INTERFACE
class StatusEnum(str, Enum):
    """Allowed status values for a ServiceRequest."""
    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


# PUBLIC_INTERFACE
class ErrorInfo(BaseModel):
    """Standard error info object carried in ErrorResponse."""
    code: str = Field(..., description="Stable string error identifier")
    message: str = Field(..., description="Human-readable error message")
    details: dict = Field(default_factory=dict, description="Optional structured details")


# PUBLIC_INTERFACE
class ErrorResponse(BaseModel):
    """Consistent JSON error envelope returned by the API."""
    error: ErrorInfo = Field(..., description="Error metadata")


# PUBLIC_INTERFACE
class Pagination(BaseModel):
    """Basic pagination input."""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")


# PUBLIC_INTERFACE
class ServiceRequestCreate(BaseModel):
    """
    Payload to create a new service request.

    Minimal fields for initial support; extend later with requester, priority, etc.
    """
    title: constr(min_length=3, max_length=120) = Field(
        ..., description="Short title for the service request (3-120 chars)"
    )
    description: Optional[constr(min_length=1, max_length=5000)] = Field(
        None, description="Detailed description of the service request (1-5000 chars if provided)"
    )
    customer_id: Optional[Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{3,64}$")]] = Field(
        None, description="Optional customer identifier (3-64, A-Za-z0-9_-)"
    )


# PUBLIC_INTERFACE
class StatusUpdateCreate(BaseModel):
    """
    Payload to update the status of an existing service request.

    Uses a strict enum for valid statuses and optional note.
    Additional business rule validations enforced at service layer.
    """
    status: StatusEnum = Field(..., description="New status for the service request")
    note: Optional[constr(min_length=1, max_length=2000)] = Field(
        None, description="Optional note explaining the status change (1-2000 chars if provided)"
    )


# PUBLIC_INTERFACE
class StatusUpdateOut(BaseModel):
    """Represents a stored status update entry."""
    status: StatusEnum = Field(..., description="Status value at this point in time")
    note: Optional[str] = Field(None, description="Associated note for the update")
    at: datetime = Field(..., description="Timestamp when the update was recorded")


# PUBLIC_INTERFACE
class ServiceRequestOut(BaseModel):
    """Canonical response model representing a service request."""
    id: str = Field(..., description="Unique identifier of the service request")
    title: str = Field(..., description="Short title")
    description: Optional[str] = Field(None, description="Detailed description")
    status: StatusEnum = Field(..., description="Current status of the request")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    customer_id: Optional[str] = Field(
        None,
        description="Customer identifier associated with the request (optional for in-memory demo)",
    )


# PUBLIC_INTERFACE
class ServiceRequestListItem(BaseModel):
    """List item representation of a service request."""
    id: str = Field(..., description="Unique identifier of the service request")
    title: str = Field(..., description="Short title")
    description: Optional[str] = Field(None, description="Detailed description")
    status: StatusEnum = Field(..., description="Current status of the request")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    customer_id: Optional[str] = Field(
        None,
        description="Customer identifier associated with the request (optional for in-memory demo)",
    )


# PUBLIC_INTERFACE
class ServiceRequestListResponse(BaseModel):
    """
    Response model for listing service requests with pagination metadata.
    """
    items: List[ServiceRequestListItem] = Field(
        default_factory=list, description="List of service requests"
    )
    total: int = Field(..., description="Total count of matching records")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")


# PUBLIC_INTERFACE
class ListRequestFilters(BaseModel):
    """
    Validated input model for list filters, pagination, and sorting.

    - Supports optional filters: status, q (free-text), customer_id,
      created_from/to (date range).
    - Pagination: page >=1, page_size in [1,100].
    - Sorting: fixed created_at desc ordering (implicit).
    """
    status: Optional[StatusEnum] = Field(None, description="Filter by status")
    q: Optional[constr(min_length=1, max_length=256)] = Field(
        None,
        description="Case-insensitive substring search across title and description (1-256 chars if provided)",
    )
    customer_id: Optional[Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{3,64}$")]] = Field(
        None, description="Filter by customer id (3-64, A-Za-z0-9_-)"
    )
    created_from: Optional[date] = Field(
        None,
        description="Filter records created on/after this date (inclusive, UTC)",
    )
    created_to: Optional[date] = Field(
        None,
        description="Filter records created on/before this date (inclusive, UTC)",
    )
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")

    @field_validator("created_to")
    @classmethod
    def _validate_date_range(cls, v: Optional[date], values: dict):
        cf: Optional[date] = values.get("created_from")
        if v is not None and cf is not None and v < cf:
            raise ValueError("created_to must be on or after created_from")
        return v


# PUBLIC_INTERFACE
class ServiceRequestHistoryEntry(BaseModel):
    """
    Single history entry for a service request status update.
    """
    status: StatusEnum = Field(..., description="Status value at this point in time")
    note: Optional[str] = Field(None, description="Associated note for the update")
    at: datetime = Field(..., description="Timestamp when the update was recorded")


# PUBLIC_INTERFACE
class ServiceRequestHistoryResponse(BaseModel):
    """
    Response model representing the chronological history of a service request.
    """
    id: str = Field(..., description="Service request identifier")
    history: List[ServiceRequestHistoryEntry] = Field(
        default_factory=list, description="Chronological list of status updates"
    )
