import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.payments.models import InvoiceStatus, PaymentStatus, PaymentMethod


# --- Invoice DTOs ---

class InvoiceCreate(BaseModel):
    unit_id: uuid.UUID
    billing_period: str = Field(..., json_schema_extra={"example": "2026-10"})
    title: str = Field(..., json_schema_extra={"example": "Monthly Maintenance - Oct 2026"})
    description: Optional[str] = None
    amount: float = Field(..., gt=0, json_schema_extra={"example": 3500.0})
    due_date: datetime


class BulkInvoiceGenerateRequest(BaseModel):
    billing_period: str = Field(..., json_schema_extra={"example": "2026-10"})
    title: str = Field(..., json_schema_extra={"example": "Monthly Maintenance - Oct 2026"})
    amount: float = Field(..., gt=0, json_schema_extra={"example": 3500.0})
    due_date_days: int = Field(default=15, ge=1, le=90, json_schema_extra={"example": 15})
    building_id: Optional[uuid.UUID] = None
    description: Optional[str] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    society_id: uuid.UUID
    unit_id: uuid.UUID
    billing_period: str
    title: str
    description: Optional[str] = None
    amount: float
    due_date: datetime
    penalty_amount: float = 0.0
    status: str
    created_at: datetime


# --- Payment Transaction DTOs ---

class InitiateOnlinePaymentRequest(BaseModel):
    invoice_id: uuid.UUID
    amount: Optional[float] = Field(default=None, gt=0)
    payment_method: str = Field(
        default=PaymentMethod.ONLINE_MOCK.value,
        json_schema_extra={"example": "online_mock"},
    )


class InitiateOnlinePaymentResponse(BaseModel):
    payment_id: uuid.UUID
    gateway_order_id: str
    amount: float
    currency: str = "INR"
    status: str
    provider: str


class VerifyOnlinePaymentRequest(BaseModel):
    payment_id: uuid.UUID
    gateway_order_id: str
    gateway_payment_id: str
    gateway_signature: str


class SubmitOfflinePaymentRequest(BaseModel):
    invoice_id: uuid.UUID
    amount: float = Field(..., gt=0, json_schema_extra={"example": 3500.0})
    payment_method: str = Field(
        default=PaymentMethod.OFFLINE_UPI_NEFT.value,
        json_schema_extra={"example": "offline_upi_neft"},
    )
    transaction_reference: str = Field(
        ..., min_length=4, json_schema_extra={"example": "UTR9876543210"}
    )
    description: Optional[str] = None


class ReviewOfflinePaymentRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    society_id: uuid.UUID
    invoice_id: Optional[uuid.UUID] = None
    unit_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    amount: float
    payment_method: str
    status: str
    transaction_reference: Optional[str] = None
    description: Optional[str] = None
    approved_by: Optional[uuid.UUID] = None
    rejection_reason: Optional[str] = None
    created_at: datetime


# --- Receipt DTOs ---

class ReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    payment_id: uuid.UUID
    receipt_number: str
    invoice_id: Optional[uuid.UUID] = None
    amount_paid: float
    payment_date: datetime
    issued_to_name: str
    unit_number: Optional[str] = None
    society_name: str
    created_at: datetime


# --- Accounting / Metrics DTOs ---

class SocietyCollectionSummary(BaseModel):
    total_invoiced: float
    total_collected: float
    total_pending: float
    pending_approval_count: int
