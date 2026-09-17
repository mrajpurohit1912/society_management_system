import uuid
import secrets
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Type, Optional
import structlog

from app.authentication.models import (
    UserModel,
    AuthCredentialModel,
    ActivationTokenModel,
    UserAccountStatus,
    UserRole,
    TokenType,
)
from app.societies.models import UserSocietyRoleModel, SubscriptionModel, SubscriptionStatus, SocietyModel
from app.authentication.repository import UserRepository
from app.societies.repository import SocietyRepository
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
from app.authentication.strategies import (
    SignupStrategy,
    UsernamePasswordStrategy,
    EmailPasswordStrategy,
    MobileOTPStrategy,
    GoogleStrategy,
    AdminSignupStrategy,
    SigninStrategy,
    UsernameSigninStrategy,
    EmailPasswordSigninStrategy,
    MobileOTPSigninStrategy,
    GoogleSigninStrategy,
)
from app.authentication.security import PasswordHasher, TokenService
from app.core.email_service import EmailService
from app.core.cache import RedisService
from app.core.config import settings

logger = structlog.get_logger(__name__)

def _ensure_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

class AuthFlowService:

    @classmethod
    async def resident_signup(cls, db: AsyncSession, payload: ResidentSignupRequest) -> UserModel:
        user_repo = UserRepository(db)
        existing_cred = await user_repo.get_credential_by_identifier("email", payload.email)
        if existing_cred:
            raise ValueError(f"An account with email '{payload.email}' already exists")

        hashed_password = PasswordHasher.hash_password(payload.password)

        user = await user_repo.create_user(
            first_name=payload.first_name,
            last_name=payload.last_name,
            role=UserRole.RESIDENT.value,
            status=UserAccountStatus.REGISTERED.value,
            email_verified=False,
        )

        await user_repo.add_credential(
            user_id=user.user_id,
            provider="email",
            identifier=payload.email,
            password_hash=hashed_password,
        )

        raw_token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        await user_repo.create_activation_token(
            user_id=user.user_id,
            token=raw_token,
            token_type=TokenType.EMAIL_VERIFICATION.value,
            expires_at=expiry,
        )

        EmailService.send_resident_verification_email(
            to_email=payload.email,
            name=f"{payload.first_name} {payload.last_name}",
            token=raw_token,
        )

        logger.info("auth.resident_signup_success", user_id=str(user.user_id), email=payload.email)
        return user

    @classmethod
    async def verify_email(cls, db: AsyncSession, payload: VerifyEmailRequest) -> UserModel:
        user_repo = UserRepository(db)
        token_record = await user_repo.get_valid_activation_token(
            token=payload.token,
            token_type=TokenType.EMAIL_VERIFICATION.value,
        )
        if not token_record:
            raise ValueError("Invalid or expired email verification token")

        if _ensure_timezone(token_record.expires_at) < datetime.now(timezone.utc):
            raise ValueError("Email verification token has expired. Please request a new one.")

        user = await user_repo.get_user_by_id(token_record.user_id)
        if not user:
            raise ValueError("User associated with token not found")

        await user_repo.update_user(user, email_verified=True, status=UserAccountStatus.EMAIL_VERIFIED.value)
        await user_repo.mark_token_used(token_record)

        logger.info("auth.email_verified_success", user_id=str(user.user_id))
        return user

    @classmethod
    async def activate_admin(cls, db: AsyncSession, payload: AdminActivateRequest) -> UserModel:
        user_repo = UserRepository(db)
        token_record = await user_repo.get_valid_activation_token(
            token=payload.token,
            token_type=TokenType.ADMIN_ACTIVATION.value,
        )
        if not token_record:
            raise ValueError("Invalid or expired admin activation token")

        if _ensure_timezone(token_record.expires_at) < datetime.now(timezone.utc):
            raise ValueError("Admin activation token has expired. Contact platform support.")

        user = await user_repo.get_user_by_id(token_record.user_id)
        if not user:
            raise ValueError("User account not found")

        cred = await user_repo.get_credential_by_user_id(user.user_id)
        if not cred:
            raise ValueError("User auth credentials record missing")

        hashed_password = PasswordHasher.hash_password(payload.password)
        await user_repo.update_credential_password(cred, hashed_password)
        await user_repo.update_user(user, status=UserAccountStatus.ACTIVE.value)
        await user_repo.mark_token_used(token_record)

        logger.info("auth.admin_activated_success", user_id=str(user.user_id))
        return user

    @classmethod
    async def unified_login(cls, db: AsyncSession, payload: UnifiedLoginRequest) -> dict:
        user_repo = UserRepository(db)
        society_repo = SocietyRepository(db)

        cred = await user_repo.get_credential_by_identifier("email", payload.email)
        if not cred or not cred.password_hash:
            raise ValueError("Invalid email or password")

        if not PasswordHasher.verify_password(payload.password, cred.password_hash):
            raise ValueError("Invalid email or password")

        user = await user_repo.get_user_by_id(cred.user_id)
        if not user:
            raise ValueError("Invalid email or password")

        if user.status == UserAccountStatus.SUSPENDED.value:
            raise ValueError("Your account has been suspended. Contact support.")

        memberships = await society_repo.list_user_memberships(user.user_id)

        active_society_id = None
        society_role = user.role
        membership_status = "unlinked"

        if memberships:
            active_mem = memberships[0]
            active_society_id = str(active_mem.society_id)
            society_role = active_mem.role
            membership_status = active_mem.status

            sub = await society_repo.get_subscription(active_mem.society_id)
            if sub and _ensure_timezone(sub.expiry_date) < datetime.now(timezone.utc):
                sub.status = SubscriptionStatus.EXPIRED.value
                logger.warning("auth.login_society_subscription_expired", society_id=str(active_mem.society_id))

        access_token = TokenService.create_access_token(str(user.user_id), user.role)

        return {
            "access_token": access_token,
            "user": {
                "user_id": str(user.user_id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": payload.email,
                "role": user.role,
                "status": user.status,
                "email_verified": user.email_verified,
                "active_society_id": active_society_id,
                "society_role": society_role,
                "membership_status": membership_status,
            },
        }



class AuthOrchestratorService:
    def __init__(self, redis_service: RedisService, google_client_id: str):
        self._strategies: Dict[Type[BaseModel], SignupStrategy] = {}
        self.register(UsernamePasswordSignupRequest, UsernamePasswordStrategy())
        self.register(EmailPasswordSignupRequest, EmailPasswordStrategy())
        self.register(MobileOTPSignupRequest, MobileOTPStrategy(redis_service))
        self.register(GoogleSignupRequest, GoogleStrategy(google_client_id))
        self.register(AdminSignupRequest, AdminSignupStrategy(settings.ADMIN_REGISTRATION_SECRET))

    def register(self, payload_type: Type[BaseModel], strategy: SignupStrategy) -> None:
        self._strategies[payload_type] = strategy

    async def execute_signup(self, db: AsyncSession, payload: BaseModel) -> UserModel:
        strategy = self._strategies.get(type(payload))
        if not strategy:
            raise ValueError(f"No authentication strategy configured for request payload of type {type(payload).__name__}")
        return await strategy.signup(db, payload)


class LoginOrchestratorService:
    def __init__(self, redis_service: RedisService, google_client_id: str):
        self._strategies: Dict[Type[BaseModel], SigninStrategy] = {}
        self.register(UsernameSigninRequest, UsernameSigninStrategy())
        self.register(EmailPasswordSigninRequest, EmailPasswordSigninStrategy())
        self.register(MobileOTPSigninRequest, MobileOTPSigninStrategy(redis_service))
        self.register(GoogleSigninRequest, GoogleSigninStrategy(google_client_id))

    def register(self, payload_type: Type[BaseModel], strategy: SigninStrategy) -> None:
        self._strategies[payload_type] = strategy

    async def execute_signin(self, db: AsyncSession, payload: BaseModel) -> UserModel:
        strategy = self._strategies.get(type(payload))
        if not strategy:
            raise ValueError(f"No signin strategy configured for request payload of type {type(payload).__name__}")
        return await strategy.signin(db, payload)
