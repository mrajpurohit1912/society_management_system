import uuid
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, ForeignKey, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VisitorType(str, enum.Enum):
    GUEST = "guest"
    DELIVERY = "delivery"
    CAB = "cab"
    SERVICE = "service"
    OTHER = "other"


class VisitorPassStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPLETED = "completed"


class VisitorLogStatus(str, enum.Enum):
    INSIDE = "inside"
    CHECKED_OUT = "checked_out"
    REJECTED = "rejected"


class EntryType(str, enum.Enum):
    PRE_APPROVED = "pre_approved"
    QUICK_CHECKIN = "quick_checkin"
    WALK_IN = "walk_in"


class VisitorPassModel(Base):
    __tablename__ = "visitor_passes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    visitor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    visitor_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    visitor_type: Mapped[str] = mapped_column(
        String(30), default=VisitorType.GUEST.value, nullable=False
    )
    passcode: Mapped[str] = mapped_column(String(6), index=True, nullable=False)
    qr_code_token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default=VisitorPassStatus.ACTIVE.value, nullable=False
    )

    vehicle_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    expected_delivery_company: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    society: Mapped["SocietyModel"] = relationship("SocietyModel")
    unit: Mapped["UnitModel"] = relationship("UnitModel")
    creator: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[created_by_user_id])
    logs: Mapped[List["VisitorLogModel"]] = relationship(
        "VisitorLogModel", back_populates="pass_record", cascade="all, delete-orphan"
    )


class VisitorLogModel(Base):
    __tablename__ = "visitor_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )
    pass_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visitor_passes.id", ondelete="SET NULL"), nullable=True
    )

    visitor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    visitor_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    visitor_type: Mapped[str] = mapped_column(
        String(30), default=VisitorType.GUEST.value, nullable=False
    )
    entry_type: Mapped[str] = mapped_column(
        String(30), default=EntryType.PRE_APPROVED.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default=VisitorLogStatus.INSIDE.value, nullable=False
    )

    vehicle_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gate_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    check_in_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    check_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    checked_in_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    checked_out_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    pass_record: Mapped[Optional["VisitorPassModel"]] = relationship(
        "VisitorPassModel", back_populates="logs"
    )
    society: Mapped["SocietyModel"] = relationship("SocietyModel")
    unit: Mapped["UnitModel"] = relationship("UnitModel")
    guard_in: Mapped[Optional["UserModel"]] = relationship("UserModel", foreign_keys=[checked_in_by])
    guard_out: Mapped[Optional["UserModel"]] = relationship("UserModel", foreign_keys=[checked_out_by])
