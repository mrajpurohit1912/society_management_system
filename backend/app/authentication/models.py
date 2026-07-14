import enum
from datetime import datetime
import uuid
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"

class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.MEMBER.value, server_default=UserRole.MEMBER.value, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    credentials: Mapped[List["AuthCredentialModel"]] = relationship(
        "AuthCredentialModel", back_populates="user", cascade="all, delete-orphan", lazy="raise"
    )
    refresh_tokens: Mapped[List["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan", lazy="raise"
    )


class AuthCredentialModel(Base):
    __tablename__ = "auth_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)     # 'username', 'email', 'phone', 'google'
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # email, phone, or google sub id
    
    # Nullable to support Google OAuth / OTP signups
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
