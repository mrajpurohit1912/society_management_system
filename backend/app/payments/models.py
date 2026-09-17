import uuid
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Float, DateTime, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    INITIATED = "initiated"
    PENDING_APPROVAL = "pending_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class PaymentMethod(str, enum.Enum):
    OFFLINE_UPI_NEFT = "offline_upi_neft"
    OFFLINE_CHEQUE = "offline_cheque"
    OFFLINE_CASH = "offline_cash"
    ONLINE_MOCK = "online_mock"
    ONLINE_RAZORPAY = "online_razorpay"


class MaintenanceInvoiceModel(Base):
    __tablename__ = "maintenance_invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )
    billing_period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., '2026-10'
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    penalty_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default=InvoiceStatus.PENDING.value, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    society: Mapped["SocietyModel"] = relationship("SocietyModel")
    unit: Mapped["UnitModel"] = relationship("UnitModel")
    payments: Mapped[List["PaymentModel"]] = relationship(
        "PaymentModel", back_populates="invoice", cascade="all, delete-orphan"
    )


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    society_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("maintenance_invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    unit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("units.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(30), default=PaymentMethod.OFFLINE_UPI_NEFT.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default=PaymentStatus.INITIATED.value, nullable=False
    )
    transaction_reference: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # UTR, Cheque No, or Online Txn ID
    gateway_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gateway_payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
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
    invoice: Mapped[Optional["MaintenanceInvoiceModel"]] = relationship(
        "MaintenanceInvoiceModel", back_populates="payments"
    )
    user: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[user_id])
    approver: Mapped[Optional["UserModel"]] = relationship(
        "UserModel", foreign_keys=[approved_by]
    )
    receipt: Mapped[Optional["PaymentReceiptModel"]] = relationship(
        "PaymentReceiptModel", back_populates="payment", uselist=False, cascade="all, delete-orphan"
    )


class PaymentReceiptModel(Base):
    __tablename__ = "payment_receipts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False)
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    issued_to_name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    society_name: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    payment: Mapped["PaymentModel"] = relationship("PaymentModel", back_populates="receipt")
