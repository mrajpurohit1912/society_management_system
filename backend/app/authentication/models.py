import enum
from datetime import datetime
import uuid
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, func, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    PLATFORM_ADMIN = "platform_admin"
    SOCIETY_ADMIN = "society_admin"
    COMMITTEE = "committee"
    RESIDENT = "resident"
    SECURITY_GUARD = "security_guard"
    MEMBER = "member"

class UserAccountStatus(str, enum.Enum):
    REGISTERED = "registered"
    EMAIL_VERIFIED = "email_verified"
    ACTIVATION_PENDING = "activation_pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class TokenType(str, enum.Enum):
    EMAIL_VERIFICATION = "email_verification"
    ADMIN_ACTIVATION = "admin_activation"
    PASSWORD_RESET = "password_reset"

class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default=UserRole.RESIDENT.value, server_default=UserRole.RESIDENT.value, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=UserAccountStatus.REGISTERED.value, server_default=UserAccountStatus.REGISTERED.value, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    credentials: Mapped[List["AuthCredentialModel"]] = relationship(
        "AuthCredentialModel", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    refresh_tokens: Mapped[List["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    activation_tokens: Mapped[List["ActivationTokenModel"]] = relationship(
        "ActivationTokenModel", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )


class AuthCredentialModel(Base):
    __tablename__ = "auth_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)     # 'username', 'email', 'phone', 'google'
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # email, phone, or google sub id
    
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) 
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="credentials")


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["UserModel"] = relationship("UserModel")


class ActivationTokenModel(Base):
    __tablename__ = "activation_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # email_verification, admin_activation
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="activation_tokens")
