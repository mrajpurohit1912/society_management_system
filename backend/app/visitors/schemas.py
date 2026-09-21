import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.visitors.models import (
    VisitorType,
    VisitorPassStatus,
    VisitorLogStatus,
    EntryType,
)


# --- Pass DTOs ---

class VisitorPassCreate(BaseModel):
    unit_id: uuid.UUID
    visitor_name: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "Aarav Sharma"})
    visitor_phone: str = Field(..., min_length=7, max_length=20, json_schema_extra={"example": "+919876543210"})
    visitor_type: str = Field(default=VisitorType.GUEST.value, json_schema_extra={"example": "guest"})
    valid_hours: Optional[int] = Field(default=12, ge=1, le=168, json_schema_extra={"example": 12})
    valid_from: Optional[datetime] = None
    vehicle_number: Optional[str] = Field(default=None, json_schema_extra={"example": "MH01AB1234"})
    expected_delivery_company: Optional[str] = Field(default=None, json_schema_extra={"example": "Amazon"})
    notes: Optional[str] = None


class VisitorPassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    society_id: uuid.UUID
    unit_id: uuid.UUID
    created_by_user_id: uuid.UUID
    visitor_name: str
    visitor_phone: str
    visitor_type: str
    passcode: str
    qr_code_token: str
    valid_from: datetime
    valid_until: datetime
    status: str
    vehicle_number: Optional[str] = None
    expected_delivery_company: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


# --- Gatekeeper Verification & Check-In DTOs ---

class PasscodeCheckInRequest(BaseModel):
    passcode: str = Field(..., min_length=6, max_length=6, json_schema_extra={"example": "849201"})
    gate_number: Optional[str] = Field(default=None, json_schema_extra={"example": "Gate 1 - Main"})


class QRCheckInRequest(BaseModel):
    qr_token: str = Field(..., min_length=16, json_schema_extra={"example": "abc123token..."})
    gate_number: Optional[str] = Field(default=None, json_schema_extra={"example": "Gate 1 - Main"})


class QuickCheckInRequest(BaseModel):
    unit_id: uuid.UUID
    visitor_name: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "Ramesh Delivery"})
    visitor_phone: str = Field(..., min_length=7, max_length=20, json_schema_extra={"example": "+919123456780"})
    visitor_type: str = Field(default=VisitorType.DELIVERY.value, json_schema_extra={"example": "delivery"})
    company_name: Optional[str] = Field(default=None, json_schema_extra={"example": "Swiggy"})
    vehicle_number: Optional[str] = Field(default=None, json_schema_extra={"example": "MH02CD5678"})
    gate_number: Optional[str] = Field(default="Gate 1", json_schema_extra={"example": "Gate 1 - North"})


class CheckOutRequest(BaseModel):
    gate_number: Optional[str] = Field(default=None, json_schema_extra={"example": "Gate 1 - Main"})


class VisitorLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    society_id: uuid.UUID
    unit_id: uuid.UUID
    pass_id: Optional[uuid.UUID] = None
    visitor_name: str
    visitor_phone: str
    visitor_type: str
    entry_type: str
    status: str
    vehicle_number: Optional[str] = None
    company_name: Optional[str] = None
    gate_number: Optional[str] = None
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    checked_in_by: Optional[uuid.UUID] = None
    checked_out_by: Optional[uuid.UUID] = None
    rejection_reason: Optional[str] = None
    created_at: datetime


# --- Metrics & Overstay Summary DTOs ---

class ActiveVisitorsSummary(BaseModel):
    total_inside: int
    deliveries_inside: int
    cabs_inside: int
    guests_inside: int
    services_inside: int
    overstay_count: int
