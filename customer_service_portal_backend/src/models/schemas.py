from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StrictInt, StrictStr, field_validator
from pydantic.types import constr

from .entities import Priority, RequestStatus


# PUBLIC_INTERFACE
class ServiceRequestCreate(BaseModel):
    """
    Schema for creating a new service request.

    Fields:
      - subject: Short title for the request (length 4..200).
      - description: Detailed description of the issue/question (length 11..5000).
      - customer_email: Contact email for the requester.
      - priority: Priority assigned; defaults to MEDIUM.
      - attachments: Optional list of attachment identifiers (placeholder).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "subject": "Unable to access my account",
                    "description": "I am receiving an error when trying to log in via the web portal. The error code is ERR-401.",
                    "customer_email": "jane.doe@example.com",
                    "priority": "HIGH",
                    "attachments": ["attch_123", "attch_456"],
                }
            ]
        }
    )

    subject: constr(strip_whitespace=True, min_length=4, max_length=200) = Field(
        ...,
        description="Short title describing the service request.",
        examples=["Password reset request"],
    )
    description: constr(strip_whitespace=True, min_length=11, max_length=5000) = Field(
        ...,
        description="Detailed description of the problem or inquiry.",
        examples=["I cannot reset my password because the link expires immediately after clicking."],
    )
    customer_email: EmailStr = Field(
        ...,
        description="Customer contact email.",
        examples=["customer@example.com"],
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Priority of the request.",
        examples=[Priority.MEDIUM, Priority.HIGH],
    )
    attachments: Optional[List[StrictStr]] = Field(
        default=None,
        description="Optional list of attachment identifiers (e.g., storage keys).",
        examples=[["file_abc123", "file_def456"]],
    )


# PUBLIC_INTERFACE
class ServiceRequestRead(BaseModel):
    """
    Schema returned when reading a service request.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 101,
                    "subject": "Unable to access my account",
                    "description": "I am receiving an error when trying to log in via the web portal. The error code is ERR-401.",
                    "customer_email": "jane.doe@example.com",
                    "status": "IN_PROGRESS",
                    "priority": "HIGH",
                    "created_at": "2025-01-01T10:00:00Z",
                    "updated_at": "2025-01-01T11:00:00Z",
                }
            ]
        }
    )

    id: StrictInt = Field(..., description="Unique identifier of the service request.", examples=[1])
    subject: StrictStr = Field(..., description="Short title describing the service request.", examples=["Account lockout"])
    description: StrictStr = Field(
        ..., description="Detailed description of the request.", examples=["Cannot log in, seeing error code ERR-401"]
    )
    customer_email: EmailStr = Field(..., description="Customer contact email.", examples=["customer@example.com"])
    status: RequestStatus = Field(..., description="Current status of the request.", examples=[RequestStatus.NEW])
    priority: Priority = Field(..., description="Priority of the request.", examples=[Priority.MEDIUM])
    created_at: datetime = Field(..., description="Creation timestamp (UTC).", examples=["2025-01-01T10:00:00Z"])
    updated_at: datetime = Field(..., description="Last update timestamp (UTC).", examples=["2025-01-01T11:00:00Z"])


# PUBLIC_INTERFACE
class ServiceRequestUpdateStatus(BaseModel):
    """
    Schema for updating a service request's status.

    This is typically used by support staff to transition a request and optionally
    leave a comment for the event log.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "IN_PROGRESS", "comment": "Starting investigation", "updated_by": "agent.alex@example.com"},
                {"status": "RESOLVED", "comment": "Credentials reset and verified by customer.", "updated_by": "agent.lee"},
            ]
        }
    )

    status: RequestStatus = Field(..., description="New status to set on the request.")
    comment: Optional[constr(strip_whitespace=True, max_length=2000)] = Field(
        default=None, description="Optional comment describing the transition or context."
    )
    updated_by: StrictStr = Field(
        ...,
        description="Identifier of the staff member performing the update (e.g., username or email).",
        examples=["agent.jordan@example.com"],
    )


# PUBLIC_INTERFACE
class ServiceRequestListFilters(BaseModel):
    """
    Query filter schema for listing service requests with pagination.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "NEW",
                    "customer_email": "jane.doe@example.com",
                    "date_from": "2025-01-01T00:00:00Z",
                    "date_to": "2025-01-31T23:59:59Z",
                    "limit": 20,
                    "offset": 0,
                },
                {"priority": "HIGH", "limit": 50, "offset": 10},
            ]
        }
    )

    status: Optional[RequestStatus] = Field(default=None, description="Filter by status.")
    priority: Optional[Priority] = Field(default=None, description="Filter by priority.")
    customer_email: Optional[EmailStr] = Field(default=None, description="Filter by customer email.")
    date_from: Optional[datetime | date] = Field(
        default=None, description="Include requests created on/after this datetime or date."
    )
    date_to: Optional[datetime | date] = Field(
        default=None, description="Include requests created on/before this datetime or date."
    )
    limit: StrictInt = Field(
        default=20,
        description="Maximum number of items to return (1..100).",
        examples=[20],
    )
    offset: StrictInt = Field(
        default=0,
        description="Number of items to skip from the beginning (>= 0).",
        examples=[0],
    )

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        if not (1 <= v <= 100):
            raise ValueError("limit must be between 1 and 100 inclusive")
        return v

    @field_validator("offset")
    @classmethod
    def validate_offset(cls, v: int) -> int:
        if v < 0:
            raise ValueError("offset must be >= 0")
        return v


# PUBLIC_INTERFACE
class RequestEventRead(BaseModel):
    """
    Schema returned when reading an event associated with a service request.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 5001,
                    "request_id": 101,
                    "status": "IN_PROGRESS",
                    "comment": "Acknowledged and investigating.",
                    "created_at": "2025-01-01T10:15:00Z",
                    "created_by": "agent.alex@example.com",
                }
            ]
        }
    )

    id: StrictInt = Field(..., description="Unique identifier of the event.", examples=[100])
    request_id: StrictInt = Field(..., description="Associated service request ID.", examples=[1])
    status: RequestStatus = Field(..., description="Status at the time of the event.", examples=[RequestStatus.NEW])
    comment: StrictStr = Field(..., description="Comment or note attached to the event.", examples=["Starting investigation"])
    created_at: datetime = Field(..., description="Event creation timestamp (UTC).", examples=["2025-01-01T10:15:00Z"])
    created_by: StrictStr = Field(
        ..., description="Identifier of the actor who created the event.", examples=["agent.alex@example.com"]
    )
