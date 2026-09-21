import uuid
import enum
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Boolean, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NoticeCategory(str, enum.Enum):
    GENERAL = "general"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"
    MEETING_AGM = "meeting_agm"
    FESTIVAL = "festival"
    FINANCIAL = "financial"
    SECURITY = "security"
    RULES = "rules"


class NoticeTargetAudience(str, enum.Enum):
    ALL = "all"
    BUILDING = "building"
    OWNERS_ONLY = "owners_only"
    TENANTS_ONLY = "tenants_only"


class NoticePriority(str, enum.Enum):
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NoticeModel(Base):
    __tablename__ = "notices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), default=NoticeCategory.GENERAL.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(20), default=NoticePriority.NORMAL.value, nullable=False
    )
    target_audience: Mapped[str] = mapped_column(
        String(30), default=NoticeTargetAudience.ALL.value, nullable=False
    )
    target_building_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buildings.id", ondelete="SET NULL"), nullable=True
    )

    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    attachments: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    society: Mapped["SocietyModel"] = relationship("SocietyModel")
    target_building: Mapped[Optional["BuildingModel"]] = relationship("BuildingModel")
    creator: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[created_by_user_id])
    read_receipts: Mapped[List["NoticeReadReceiptModel"]] = relationship(
        "NoticeReadReceiptModel",
        back_populates="notice",
        cascade="all, delete-orphan",
    )


class NoticeReadReceiptModel(Base):
    __tablename__ = "notice_read_receipts"
    __table_args__ = (
        UniqueConstraint("notice_id", "user_id", name="uq_notice_user_read"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    notice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notices.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    notice: Mapped["NoticeModel"] = relationship("NoticeModel", back_populates="read_receipts")
    user: Mapped["UserModel"] = relationship("UserModel")
