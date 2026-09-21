import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict

from app.notices.models import (
    NoticeCategory,
    NoticeTargetAudience,
    NoticePriority,
)


class NoticeCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150, json_schema_extra={"example": "Annual General Body Meeting (AGM) Notice"})
    content: str = Field(..., min_length=5, json_schema_extra={"example": "All society members are requested to attend the AGM scheduled for this Sunday at 10 AM in the Clubhouse."})
    category: str = Field(default=NoticeCategory.MEETING_AGM.value, json_schema_extra={"example": "meeting_agm"})
    priority: str = Field(default=NoticePriority.NORMAL.value, json_schema_extra={"example": "normal"})
    target_audience: str = Field(default=NoticeTargetAudience.ALL.value, json_schema_extra={"example": "all"})
    target_building_id: Optional[uuid.UUID] = Field(default=None, json_schema_extra={"example": "b1c2d3e4-..."})
    is_pinned: bool = Field(default=False, json_schema_extra={"example": True})
    expires_at: Optional[datetime] = None
    attachments: Optional[List[str]] = Field(default=None, json_schema_extra={"example": ["https://s3.amazonaws.com/bucket/agm_agenda.pdf"]})


class NoticeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=150)
    content: Optional[str] = Field(default=None, min_length=5)
    category: Optional[str] = None
    priority: Optional[str] = None
    target_audience: Optional[str] = None
    target_building_id: Optional[uuid.UUID] = None
    is_pinned: Optional[bool] = None
    expires_at: Optional[datetime] = None
    attachments: Optional[List[str]] = None


class NoticeReadReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    notice_id: uuid.UUID
    user_id: uuid.UUID
    read_at: datetime


class NoticeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    society_id: uuid.UUID
    created_by_user_id: uuid.UUID
    title: str
    content: str
    category: str
    priority: str
    target_audience: str
    target_building_id: Optional[uuid.UUID] = None
    is_pinned: bool
    expires_at: Optional[datetime] = None
    attachments: Optional[List[str]] = None
    published_at: datetime
    created_at: datetime
    updated_at: datetime
    read_count: int = 0
    is_read_by_me: bool = False


class NoticeStatsResponse(BaseModel):
    notice_id: uuid.UUID
    title: str
    total_reads: int
    recent_readers: List[NoticeReadReceiptResponse]
