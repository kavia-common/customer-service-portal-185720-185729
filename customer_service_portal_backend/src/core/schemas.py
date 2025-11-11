from typing import List, Optional
from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class ServiceRequestCreate(BaseModel):
    """
    Payload to create a new service request.

    Note:
        This is a placeholder model for scaffolding. Fields are minimal and may be
        extended in subsequent steps.
    """
    title: str = Field(..., description="Short title for the service request")
    description: Optional[str] = Field(
        None, description="Detailed description of the service request"
    )
    # TODO: Add fields like customer_id, attachments, category, priority


# PUBLIC_INTERFACE
class StatusUpdateCreate(BaseModel):
    """
    Payload to update the status of an existing service request.

    Note:
        This is a placeholder and will be refined with strict enums and metadata later.
    """
    status: str = Field(..., description="New status for the service request")
    note: Optional[str] = Field(
        None, description="Optional note explaining the status change"
    )
    # TODO: Convert 'status' to an Enum with valid transitions and add actor metadata


# PUBLIC_INTERFACE
class ServiceRequestResponse(BaseModel):
    """
    Response model representing a service request.

    Note:
        Placeholder response to support scaffolding. To be replaced with full model.
    """
    id: str = Field(..., description="Unique identifier of the service request")
    title: str = Field(..., description="Short title")
    description: Optional[str] = Field(None, description="Detailed description")
    status: str = Field(..., description="Current status of the request")
    # TODO: Add timestamps, requester info, assignee, priority, etc.


# PUBLIC_INTERFACE
class ServiceRequestListResponse(BaseModel):
    """
    Response model for listing service requests with basic pagination placeholders.
    """
    items: List[ServiceRequestResponse] = Field(
        default_factory=list, description="List of service requests"
    )
    total: int = Field(0, description="Total count of matching records (placeholder)")
    page: int = Field(1, description="Current page (placeholder)")
    page_size: int = Field(20, description="Page size (placeholder)")


# PUBLIC_INTERFACE
class ServiceRequestHistoryEntry(BaseModel):
    """
    Single history entry for a service request status update.
    """
    status: str = Field(..., description="Status value at this point in time")
    note: Optional[str] = Field(None, description="Associated note for the update")
    # TODO: Add timestamp, actor information


# PUBLIC_INTERFACE
class ServiceRequestHistoryResponse(BaseModel):
    """
    Response model representing the chronological history of a service request.
    """
    id: str = Field(..., description="Service request identifier")
    history: List[ServiceRequestHistoryEntry] = Field(
        default_factory=list, description="Chronological list of status updates"
    )
