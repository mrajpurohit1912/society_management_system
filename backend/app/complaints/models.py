import uuid
import enum
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ComplaintCategory(str, enum.Enum):
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    CARPENTRY = "carpentry"
    ELEVATOR = "elevator"
    CLEANLINESS = "cleanliness"
    SECURITY = "security"
    GARDENING = "gardening"
    AMENITY = "amenity"
    CIVIL_STRUCTURAL = "civil_structural"
    OTHER = "other"


class ComplaintScope(str, enum.Enum):
    PERSONAL_UNIT = "personal_unit"
    COMMON_AREA = "common_area"


class ComplaintPriority(str, enum.Enum):
    P1_CRITICAL = "p1_critical"  # SLA: 4 hours
    P2_HIGH = "p2_high"          # SLA: 24 hours
    P3_MEDIUM = "p3_medium"      # SLA: 48 hours
    P4_LOW = "p4_low"            # SLA: 72 hours


class ComplaintStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"


# SLA duration mapping in hours
SLA_HOURS_MAP = {
    ComplaintPriority.P1_CRITICAL.value: 4,
    ComplaintPriority.P2_HIGH.value: 24,
    ComplaintPriority.P3_MEDIUM.value: 48,
    ComplaintPriority.P4_LOW.value: 72,
}


class ComplaintTicketModel(Base):
    __tablename__ = "complaint_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("units.id", ondelete="SET NULL"), nullable=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    ticket_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    scope: Mapped[str] = mapped_column(
        String(30), default=ComplaintScope.PERSONAL_UNIT.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(20), default=ComplaintPriority.P3_MEDIUM.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default=ComplaintStatus.OPEN.value, nullable=False
    )

    common_area_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    photos: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Automated SLA tracking
    sla_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Assignment details
    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    assigned_vendor_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assigned_vendor_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Resolution & Sign-off details
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_photos: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Resident satisfaction rating & feedback
    resident_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resident_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    society: Mapped["SocietyModel"] = relationship("SocietyModel")
    unit: Mapped[Optional["UnitModel"]] = relationship("UnitModel")
    creator: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[created_by_user_id])
    assignee: Mapped[Optional["UserModel"]] = relationship("UserModel", foreign_keys=[assigned_to_user_id])
    comments: Mapped[List["ComplaintCommentModel"]] = relationship(
        "ComplaintCommentModel",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="ComplaintCommentModel.created_at",
    )


class ComplaintCommentModel(Base):
    __tablename__ = "complaint_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaint_tickets.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attachment_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    ticket: Mapped["ComplaintTicketModel"] = relationship(
        "ComplaintTicketModel", back_populates="comments"
    )
    user: Mapped["UserModel"] = relationship("UserModel")
