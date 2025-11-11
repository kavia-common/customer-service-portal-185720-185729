from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TypedDict


class RequestStatus(str, Enum):
    """
    Enumeration representing the lifecycle status of a Service Request.
    """

    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Priority(str, Enum):
    """
    Enumeration representing the priority assigned to a Service Request.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ServiceRequest(TypedDict):
    """
    Internal representation of a Service Request entity.

    This structure is used by internal layers (e.g., repositories/services)
    and is not directly exposed as the public API schema.
    """

    id: int
    subject: str
    description: str
    customer_email: str
    status: RequestStatus
    priority: Priority
    created_at: datetime
    updated_at: datetime


class RequestEvent(TypedDict):
    """
    Internal representation of a Request Event entity.

    Events capture meaningful transitions or comments associated with a
    Service Request's lifecycle.
    """

    id: int
    request_id: int
    status: RequestStatus
    comment: str
    created_at: datetime
    created_by: str
