import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from app.societies.models import SocietyStatus, BuildingStatus, UnitType, UnitStatus, ResidencyType, ResidentStatus, VehicleType, SocietyRole

# --- User & Base Config ---
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# --- Society Schemas ---
class SocietyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    registration_no: str = Field(..., min_length=2, max_length=50)
    address: str = Field(..., min_length=5, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    country: str = Field(..., min_length=2, max_length=100)
    zipcode: str = Field(..., min_length=3, max_length=20)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class SocietyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[SocietyStatus] = None

class SocietyResponse(BaseSchema):
    id: uuid.UUID
    name: str
    registration_no: str
    address: str
    city: str
    state: str
    country: str
    zipcode: str
    email: Optional[str]
    phone: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

# --- Building Schemas ---
class BuildingCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    status: Optional[BuildingStatus] = None

class BuildingResponse(BaseSchema):
    id: uuid.UUID
    society_id: uuid.UUID
    name: str
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    zipcode: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    status: str
    created_at: datetime

# --- Floor Schemas ---
class FloorCreate(BaseModel):
    floor_number: int
    floor_name: Optional[str] = None

class FloorResponse(BaseSchema):
    id: uuid.UUID
    building_id: uuid.UUID
    floor_number: int
    floor_name: Optional[str]
    created_at: datetime

# --- Unit Schemas ---
class UnitCreate(BaseModel):
    unit_number: str = Field(..., min_length=1, max_length=20)
    unit_type: UnitType = UnitType.FLAT
    status: UnitStatus = UnitStatus.VACANT

class UnitUpdate(BaseModel):
    unit_number: Optional[str] = None
    unit_type: Optional[UnitType] = None
    status: Optional[UnitStatus] = None

class UnitResponse(BaseSchema):
    id: uuid.UUID
    floor_id: uuid.UUID
    unit_number: str
    unit_type: str
    status: str
    created_at: datetime

# --- Resident Schemas ---
class ResidentAssign(BaseModel):
    user_id: uuid.UUID
    residency_type: ResidencyType = ResidencyType.TENANT
    is_primary_contact: bool = False
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ResidentUpdate(BaseModel):
    residency_type: Optional[ResidencyType] = None
    is_primary_contact: Optional[bool] = None
    status: Optional[ResidentStatus] = None
    end_date: Optional[datetime] = None

class ResidentResponse(BaseSchema):
    id: uuid.UUID
    unit_id: uuid.UUID
    user_id: uuid.UUID
    residency_type: str
    is_primary_contact: bool
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    status: str
    created_at: datetime

# --- Vehicle Schemas ---
class VehicleRegister(BaseModel):
    resident_id: Optional[uuid.UUID] = None
    vehicle_type: VehicleType = VehicleType.CAR
    registration_number: str = Field(..., min_length=3, max_length=30)

class VehicleResponse(BaseSchema):
    id: uuid.UUID
    unit_id: uuid.UUID
    resident_id: Optional[uuid.UUID]
    vehicle_type: str
    registration_number: str
    created_at: datetime

# --- Scoped Role Schemas ---
class UserSocietyRoleAssign(BaseModel):
    user_id: uuid.UUID
    role: SocietyRole = SocietyRole.MEMBER

class UserSocietyRoleResponse(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    society_id: uuid.UUID
    role: str
    created_at: datetime

# --- Bulk Provisioning Schemas ---
class BuildingProvision(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    number_of_floors: int = Field(..., ge=1, le=150)
    units_per_floor: int = Field(..., ge=1, le=50)

class BulkProvisionRequest(BaseModel):
    buildings: List[BuildingProvision]
