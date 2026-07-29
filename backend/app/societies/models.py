import uuid
import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SocietyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class LeadStatus(str, enum.Enum):
    LEAD_CREATED = "lead_created"
    CONTACTED = "contacted"
    ONBOARDED = "onboarded"

class MembershipStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    REMOVED = "removed"

class UnitType(str, enum.Enum):
    FLAT = "flat"
    VILLA = "villa"
    PENTHOUSE = "penthouse"

class UnitStatus(str, enum.Enum):
    VACANT = "vacant"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

class ResidencyType(str, enum.Enum):
    OWNER_RESIDING = "owner_residing"
    OWNER_NON_RESIDING = "owner_non_residing"
    TENANT = "tenant"
    FAMILY_MEMBER = "family_member"

class ResidentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"

class VehicleType(str, enum.Enum):
    CAR = "car"
    BIKE = "bike"
    SCOOTER = "scooter"
    OTHER = "other"

class SocietyRole(str, enum.Enum):
    ADMIN = "admin"
    SOCIETY_ADMIN = "society_admin"
    COMMITTEE = "committee"
    RESIDENT = "resident"
    SECURITY = "security"
    MEMBER = "member"


class SocietyModel(Base):
    __tablename__ = "societies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    registration_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    zipcode: Mapped[str] = mapped_column(String(20), nullable=False)
    
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=SocietyStatus.ACTIVE.value, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    buildings: Mapped[List["BuildingModel"]] = relationship("BuildingModel", back_populates="society", cascade="all, delete-orphan", lazy="selectin")
    roles: Mapped[List["UserSocietyRoleModel"]] = relationship("UserSocietyRoleModel", back_populates="society", cascade="all, delete-orphan", lazy="selectin")
    subscription: Mapped[Optional["SubscriptionModel"]] = relationship("SubscriptionModel", back_populates="society", uselist=False, cascade="all, delete-orphan", lazy="selectin")


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False, unique=True)
    plan: Mapped[str] = mapped_column(String(50), default="GOLD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SubscriptionStatus.ACTIVE.value, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_admins: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    society: Mapped["SocietyModel"] = relationship("SocietyModel", back_populates="subscription")


class SocietyLeadModel(Base):
    __tablename__ = "society_leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile: Mapped[str] = mapped_column(String(50), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    expected_flats: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_admins: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=LeadStatus.LEAD_CREATED.value, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BuildingModel(Base):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    society: Mapped["SocietyModel"] = relationship("SocietyModel", back_populates="buildings")
    floors: Mapped[List["FloorModel"]] = relationship("FloorModel", back_populates="building", cascade="all, delete-orphan", lazy="selectin")


class FloorModel(Base):
    __tablename__ = "floors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False)
    floor_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    building: Mapped["BuildingModel"] = relationship("BuildingModel", back_populates="floors")
    units: Mapped[List["UnitModel"]] = relationship("UnitModel", back_populates="floor", cascade="all, delete-orphan", lazy="selectin")


class UnitModel(Base):
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    unit_number: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(20), default=UnitType.FLAT.value, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=UnitStatus.VACANT.value, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    floor: Mapped["FloorModel"] = relationship("FloorModel", back_populates="units")
    residents: Mapped[List["UnitResidentModel"]] = relationship("UnitResidentModel", back_populates="unit", cascade="all, delete-orphan", lazy="selectin")
    vehicles: Mapped[List["VehicleModel"]] = relationship("VehicleModel", back_populates="unit", cascade="all, delete-orphan", lazy="selectin")


class UnitResidentModel(Base):
    __tablename__ = "unit_residents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    residency_type: Mapped[str] = mapped_column(String(30), default=ResidencyType.TENANT.value, nullable=False)
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=ResidentStatus.ACTIVE.value, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    unit: Mapped["UnitModel"] = relationship("UnitModel", back_populates="residents")
    user: Mapped["UserModel"] = relationship("UserModel")


class VehicleModel(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    resident_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("unit_residents.id", ondelete="SET NULL"), nullable=True)
    vehicle_type: Mapped[str] = mapped_column(String(20), default=VehicleType.CAR.value, nullable=False)
    registration_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    unit: Mapped["UnitModel"] = relationship("UnitModel", back_populates="vehicles")
    resident: Mapped[Optional["UnitResidentModel"]] = relationship("UnitResidentModel")


class UserSocietyRoleModel(Base):
    __tablename__ = "user_society_roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    unit_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("units.id", ondelete="SET NULL"), nullable=True)
    role: Mapped[str] = mapped_column(String(30), default=SocietyRole.MEMBER.value, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=MembershipStatus.PENDING.value, nullable=False)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[user_id])
    society: Mapped["SocietyModel"] = relationship("SocietyModel", back_populates="roles")
    unit: Mapped[Optional["UnitModel"]] = relationship("UnitModel")
