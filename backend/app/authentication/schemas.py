import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from enum import Enum

# --- Domain Entities ---

class AuthCredentialDomain(BaseModel):
    id: Optional[int] = None
    user_id: uuid.UUID
    provider: str
    identifier: str
    password_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserDomain(BaseModel):
    user_id: uuid.UUID
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    role: str
    status: Optional[str] = "registered"
    email_verified: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    credentials: List[AuthCredentialDomain] = []

    class Config:
        from_attributes = True


# --- Request DTOs ---

class BaseSignupRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

class ResidentSignupRequest(BaseSignupRequest):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    mobile_number: Optional[str] = None

class UsernamePasswordSignupRequest(BaseSignupRequest):
    username: str = Field(..., min_length=4, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)

class EmailPasswordSignupRequest(BaseSignupRequest):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class MobileOTPSignupRequest(BaseSignupRequest):
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    otp_code: str = Field(..., min_length=6, max_length=6)

class GoogleSignupRequest(BaseModel):
    google_id_token: str

class AdminSignupRequest(BaseSignupRequest):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    admin_secret: str

class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=10)

class AdminActivateRequest(BaseModel):
    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=8, max_length=128)

# Unified Signin Request
class UnifiedLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class UsernameSigninRequest(BaseModel):
    username: str = Field(..., min_length=4, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)

class EmailPasswordSigninRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class MobileOTPSigninRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    otp_code: str = Field(..., min_length=6, max_length=6)

class GoogleSigninRequest(BaseModel):
    google_id_token: str
