from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import uuid

class RegisterSocietyLeadRequest(BaseModel):
    organization_name: str = Field(..., json_schema_extra={"example": "Green Valley Society"})
    primary_contact_name: str = Field(..., json_schema_extra={"example": "Mahavir Rajpurohit"})
    email: EmailStr = Field(..., json_schema_extra={"example": "mahavir@example.com"})
    mobile: str = Field(..., json_schema_extra={"example": "+919876543210"})
    city: str = Field(..., json_schema_extra={"example": "Mumbai"})
    expected_flats: Optional[int] = Field(default=100, json_schema_extra={"example": 150})
    expected_admins: Optional[int] = Field(default=3, json_schema_extra={"example": 3})
    comments: Optional[str] = None

class UpdateSocietyLeadStatusRequest(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "in_discussion"})
    comments: Optional[str] = None

class PlatformCreateSocietyRequest(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Green Valley Residency"})
    registration_no: str = Field(..., json_schema_extra={"example": "RWA/MUM/2026/8921"})
    address: str = Field(..., json_schema_extra={"example": "123 Palm Avenue, Bandra West"})
    city: str = Field(..., json_schema_extra={"example": "Mumbai"})
    state: str = Field(..., json_schema_extra={"example": "Maharashtra"})
    country: str = Field(default="India", json_schema_extra={"example": "India"})
    zipcode: str = Field(..., json_schema_extra={"example": "400050"})
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class PlatformCreateSocietyFromLeadRequest(BaseModel):
    plan: Optional[str] = Field(default="GOLD", json_schema_extra={"example": "GOLD"})
    valid_months: Optional[int] = Field(default=12, json_schema_extra={"example": 12})
    registration_no: Optional[str] = Field(default=None, json_schema_extra={"example": "RWA/MUM/2026/8921"})
    address: Optional[str] = Field(default=None, json_schema_extra={"example": "123 Palm Avenue, Bandra West"})
    state: Optional[str] = Field(default="Maharashtra", json_schema_extra={"example": "Maharashtra"})
    zipcode: Optional[str] = Field(default="000000", json_schema_extra={"example": "400050"})

class PlatformCreateSubscriptionRequest(BaseModel):
    society_id: uuid.UUID
    plan: str = Field(default="GOLD", json_schema_extra={"example": "GOLD"})
    valid_months: int = Field(default=12, json_schema_extra={"example": 12})
    max_admins: int = Field(default=5, json_schema_extra={"example": 5})
    max_storage_gb: int = Field(default=10, json_schema_extra={"example": 10})

class PlatformCreateAdminRequest(BaseModel):
    society_id: uuid.UUID
    first_name: str = Field(..., json_schema_extra={"example": "John"})
    last_name: str = Field(..., json_schema_extra={"example": "Doe"})
    email: EmailStr = Field(..., json_schema_extra={"example": "admin@greenvalley.com"})
    mobile: str = Field(..., json_schema_extra={"example": "+919876543210"})
