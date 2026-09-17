from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.authentication.models import UserModel
from app.authentication.schemas import (
    EmailPasswordSignupRequest,
    EmailPasswordSigninRequest,
)
from app.authentication.repository import UserRepository
from app.authentication.security import PasswordHasher
from app.authentication.strategies.base import SignupStrategy, SigninStrategy

logger = structlog.get_logger(__name__)


class EmailPasswordStrategy(SignupStrategy[EmailPasswordSignupRequest]):
    """
    Strategy for local registration using an Email and Password.
    """

    async def signup(self, db: AsyncSession, payload: EmailPasswordSignupRequest) -> UserModel:
        repo = UserRepository(db)

        # 1. Check if email is already in use
        logger.info("strategy.email_signup_attempt", email=payload.email)
        existing_credential = await repo.get_credential_by_identifier(
            provider="email",
            identifier=payload.email,
        )
        if existing_credential:
            logger.warning("strategy.email_signup_taken", email=payload.email)
            raise ValueError("Email is already registered")

        # 2. Hash password via central PasswordHasher
        hashed_password = PasswordHasher.hash_password(payload.password)

        # 3. Save to DB
        user = await repo.create_user_with_credentials(
            first_name=payload.first_name,
            last_name=payload.last_name,
            provider="email",
            identifier=payload.email,
            password_hash=hashed_password,
        )

        return user


class EmailPasswordSigninStrategy(SigninStrategy[EmailPasswordSigninRequest]):
    """
    Strategy for local authentication using an Email and Password.
    """

    async def signin(self, db: AsyncSession, payload: EmailPasswordSigninRequest) -> UserModel:
        repo = UserRepository(db)
        logger.info("strategy.email_signin_attempt", email=payload.email)

        result = await repo.get_user_by_credential(provider="email", identifier=payload.email)
        if not result:
            logger.warning("strategy.email_signin_failed_missing_user", email=payload.email)
            raise ValueError("Invalid email or password")

        user, credential = result
        if not credential.password_hash:
            logger.warning("strategy.email_signin_failed_missing_hash", email=payload.email)
            raise ValueError("Invalid email or password")

        is_valid = PasswordHasher.verify_password(payload.password, credential.password_hash)
        if not is_valid:
            logger.warning("strategy.email_signin_failed_bad_password", email=payload.email)
            raise ValueError("Invalid email or password")

        return user
