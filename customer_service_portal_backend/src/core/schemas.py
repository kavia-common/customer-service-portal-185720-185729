from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class StatusEnum(str, Enum):
    """Allowed status values for a ServiceRequest."""
    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


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
    title: str = Field(..., min_length=1, description="Short title for the service request")
    description: Optional[str] = Field(
        None, description="Detailed description of the service request"
    )


# PUBLIC_INTERFACE
class StatusUpdateCreate(BaseModel):
    """
    Payload to update the status of an existing service request.

    Uses a strict enum for valid statuses and optional note.
    """
    status: StatusEnum = Field(..., description="New status for the service request")
    note: Optional[str] = Field(None, description="Optional note explaining the status change")


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


# PUBLIC_INTERFACE
class ServiceRequestListItem(ServiceRequestOut):
    """List item representation of a service request."""
    pass


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
