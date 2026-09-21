import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.complaints.models import (
    ComplaintCategory,
    ComplaintScope,
    ComplaintPriority,
    ComplaintStatus,
)


class ComplaintCreate(BaseModel):
    unit_id: Optional[uuid.UUID] = Field(default=None, json_schema_extra={"example": "a1b2c3d4-..."})
    title: str = Field(..., min_length=3, max_length=150, json_schema_extra={"example": "Water leakage in master bathroom"})
    description: str = Field(..., min_length=5, json_schema_extra={"example": "The faucet in the master bathroom is continuously leaking causing water accumulation."})
    category: str = Field(default=ComplaintCategory.PLUMBING.value, json_schema_extra={"example": "plumbing"})
    scope: str = Field(default=ComplaintScope.PERSONAL_UNIT.value, json_schema_extra={"example": "personal_unit"})
    priority: str = Field(default=ComplaintPriority.P3_MEDIUM.value, json_schema_extra={"example": "p3_medium"})
    common_area_location: Optional[str] = Field(default=None, json_schema_extra={"example": "Tower B Ground Floor Lobby"})
    photos: Optional[List[str]] = Field(default=None, json_schema_extra={"example": ["https://s3.amazonaws.com/bucket/leak.jpg"]})


class ComplaintAssignRequest(BaseModel):
    assigned_to_user_id: Optional[uuid.UUID] = None
    assigned_vendor_name: Optional[str] = Field(default=None, max_length=100, json_schema_extra={"example": "QuickFix Plumbing Services"})
    assigned_vendor_phone: Optional[str] = Field(default=None, max_length=20, json_schema_extra={"example": "+919876543210"})
    notes: Optional[str] = None


class ComplaintStatusUpdateRequest(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "in_progress"})
    notes: Optional[str] = None


class ComplaintResolveRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=3, json_schema_extra={"example": "Replaced the damaged washer valve in the master faucet. Leakage resolved."})
    resolution_photos: Optional[List[str]] = None


class ComplaintCloseRequest(BaseModel):
    resident_rating: int = Field(..., ge=1, le=5, json_schema_extra={"example": 5})
    resident_feedback: Optional[str] = Field(default=None, json_schema_extra={"example": "Very prompt service by the plumber. Highly satisfied!"})


class ComplaintCommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, json_schema_extra={"example": "The technician visited at 4 PM and inspected the valve."})
    is_internal: bool = Field(default=False, json_schema_extra={"example": False})
    attachment_url: Optional[str] = None


class ComplaintCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticket_id: uuid.UUID
    user_id: uuid.UUID
    comment: str
    is_internal: bool
    attachment_url: Optional[str] = None
    created_at: datetime


class ComplaintTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    society_id: uuid.UUID
    unit_id: Optional[uuid.UUID] = None
    created_by_user_id: uuid.UUID
    ticket_number: str
    title: str
    description: str
    category: str
    scope: str
    priority: str
    status: str
    common_area_location: Optional[str] = None
    photos: Optional[List[str]] = None
    sla_deadline: datetime
    is_overdue: bool = False
    assigned_to_user_id: Optional[uuid.UUID] = None
    assigned_vendor_name: Optional[str] = None
    assigned_vendor_phone: Optional[str] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolution_photos: Optional[List[str]] = None
    resident_rating: Optional[int] = None
    resident_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    comments_count: int = 0


class ComplaintSummaryMetrics(BaseModel):
    total_tickets: int
    open_tickets: int
    assigned_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    overdue_sla_tickets: int
    average_rating: Optional[float] = None
    by_category: Dict[str, int]
