import os
import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.cache import RedisService
from app.core.logging_context import set_logging_context
from app.authentication.schemas import (
    ResidentSignupRequest,
    VerifyEmailRequest,
    AdminActivateRequest,
    UnifiedLoginRequest,
    UsernamePasswordSignupRequest,
    EmailPasswordSignupRequest,
    MobileOTPSignupRequest,
    GoogleSignupRequest,
    AdminSignupRequest,
    UsernameSigninRequest,
    EmailPasswordSigninRequest,
    MobileOTPSigninRequest,
    GoogleSigninRequest,
)
from app.authentication.services import AuthFlowService, AuthOrchestratorService, LoginOrchestratorService
from app.authentication.security import TokenService
from app.authentication.repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication & User Onboarding"])
logger = structlog.get_logger(__name__)

redis_service = RedisService()
google_client_id = os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id")
orchestrator = AuthOrchestratorService(redis_service, google_client_id)
login_orchestrator = LoginOrchestratorService(redis_service, google_client_id)

async def get_orchestrator() -> AuthOrchestratorService:
    return orchestrator

async def get_login_orchestrator() -> LoginOrchestratorService:
    return login_orchestrator


@router.post("/resident/signup", status_code=status.HTTP_201_CREATED)
async def resident_signup(
    payload: ResidentSignupRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Public Resident Signup: Registers identity and sends an email verification link via Resend.
    Does NOT assign a society membership until the user requests & gets approved.
    """
    try:
        async with db.begin():
            user = await AuthFlowService.resident_signup(db, payload)
        return {
            "success": True,
            "message": "Resident signup successful. A verification email has been sent to your email address.",
            "data": {
                "user_id": str(user.user_id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "status": user.status,
                "email_verified": user.email_verified,
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify-email")
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Verifies user's email address using the token delivered via Resend email.
    """
    try:
        async with db.begin():
            user = await AuthFlowService.verify_email(db, payload)
        return {
            "success": True,
            "message": "Email verified successfully! You can now log in.",
            "data": {
                "user_id": str(user.user_id),
                "email_verified": user.email_verified,
                "status": user.status,
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/activate")
async def activate_admin(
    payload: AdminActivateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Admin Account Activation: Allows provisioned Society Admin to set their password and activate their account.
    """
    try:
        async with db.begin():
            user = await AuthFlowService.activate_admin(db, payload)
        return {
            "success": True,
            "message": "Admin account activated successfully! You may now sign in.",
            "data": {
                "user_id": str(user.user_id),
                "status": user.status,
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login")
async def unified_login(
    payload: UnifiedLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Unified Signin Endpoint: Single entry point for Admins, Residents, and Staff.
    Authenticates user, checks email verification & active society membership status.
    """
    try:
        async with db.begin():
            res = await AuthFlowService.unified_login(db, payload)
            
            # Configure Refresh Token Cookie
            raw_refresh, refresh_hash, expires_at = TokenService.create_refresh_token(res["user"]["user_id"])
            repo = UserRepository(db)
            await repo.add_refresh_token(
                user_id=res["user"]["user_id"],
                token_hash=refresh_hash,
                expires_at=expires_at
            )

        response.set_cookie(
            key="refresh_token",
            value=raw_refresh,
            httponly=True,
            secure=True,
            samesite="strict",
            expires=expires_at
        )

        return {
            "success": True,
            "message": "Login successful",
            "data": res
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
