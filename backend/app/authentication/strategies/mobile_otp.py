from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.authentication.models import UserModel
from app.authentication.schemas import (
    MobileOTPSignupRequest,
    MobileOTPSigninRequest,
)
from app.authentication.repository import UserRepository
from app.core.cache import RedisService
from app.authentication.strategies.base import SignupStrategy, SigninStrategy

logger = structlog.get_logger(__name__)


class MobileOTPStrategy(SignupStrategy[MobileOTPSignupRequest]):
    """
    Strategy for registration using a Mobile Number and SMS OTP.
    """

    def __init__(self, cache_service: RedisService):
        self.cache = cache_service

    async def signup(self, db: AsyncSession, payload: MobileOTPSignupRequest) -> UserModel:
        repo = UserRepository(db)
        logger.info("strategy.otp_signup_attempt", phone=payload.phone_number)

        # 1. Security check: Verify OTP matches value in Redis
        is_valid = await self.cache.verify_otp(
            phone=payload.phone_number,
            otp_code=payload.otp_code,
        )
        if not is_valid:
            logger.warning("strategy.otp_signup_invalid_otp", phone=payload.phone_number)
            raise ValueError("Invalid or expired OTP code")

        # 2. Check if phone number is already registered in DB
        existing_credential = await repo.get_credential_by_identifier(
            provider="phone",
            identifier=payload.phone_number,
        )
        if existing_credential:
            logger.warning("strategy.otp_signup_phone_taken", phone=payload.phone_number)
            raise ValueError("Phone number is already registered")

        # 3. Save user profile & link phone credential (no password)
        user = await repo.create_user_with_credentials(
            first_name=payload.first_name,
            last_name=payload.last_name,
            provider="phone",
            identifier=payload.phone_number,
            password_hash=None,
        )

        # 4. Invalidate the OTP in Redis immediately so it cannot be reused
        await self.cache.invalidate_otp(payload.phone_number)

        return user


class MobileOTPSigninStrategy(SigninStrategy[MobileOTPSigninRequest]):
    """
    Strategy for authentication using a Mobile Number and SMS OTP.
    """

    def __init__(self, cache_service: RedisService):
        self.cache = cache_service

    async def signin(self, db: AsyncSession, payload: MobileOTPSigninRequest) -> UserModel:
        logger.info("strategy.otp_signin_attempt", phone=payload.phone_number)
        is_valid = await self.cache.verify_otp(
            phone=payload.phone_number,
            otp_code=payload.otp_code,
        )
        if not is_valid:
            logger.warning("strategy.otp_signin_invalid_otp", phone=payload.phone_number)
            raise ValueError("Invalid or expired OTP code")

        repo = UserRepository(db)
        result = await repo.get_user_by_credential(provider="phone", identifier=payload.phone_number)
        if not result:
            logger.warning("strategy.otp_signin_phone_not_found", phone=payload.phone_number)
            raise ValueError("Phone number is not registered")

        user, _ = result
        await self.cache.invalidate_otp(payload.phone_number)
        return user
