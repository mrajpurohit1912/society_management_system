from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.authentication.models import UserModel
from app.authentication.schemas import AdminSignupRequest
from app.authentication.repository import UserRepository
from app.authentication.security import PasswordHasher
from app.authentication.strategies.base import SignupStrategy

logger = structlog.get_logger(__name__)


class AdminSignupStrategy(SignupStrategy[AdminSignupRequest]):
    """
    Strategy for local registration of an Admin using Email, Password, and Admin Secret.
    """

    def __init__(self, admin_secret: str):
        self.admin_secret = admin_secret

    async def signup(self, db: AsyncSession, payload: AdminSignupRequest) -> UserModel:
        repo = UserRepository(db)

        # 1. Verify the admin secret key
        logger.info("strategy.admin_signup_attempt", email=payload.email)
        if payload.admin_secret != self.admin_secret:
            logger.warning("strategy.admin_signup_invalid_secret", email=payload.email)
            raise ValueError("Invalid administrator registration secret")

        # 2. Check if email is already in use
        existing_credential = await repo.get_credential_by_identifier(
            provider="email",
            identifier=payload.email,
        )
        if existing_credential:
            logger.warning("strategy.admin_signup_taken", email=payload.email)
            raise ValueError("Email is already registered")

        # 3. Hash password via central PasswordHasher
        hashed_password = PasswordHasher.hash_password(payload.password)

        # 4. Save to DB with 'admin' role
        user = await repo.create_user_with_credentials(
            first_name=payload.first_name,
            last_name=payload.last_name,
            provider="email",
            identifier=payload.email,
            password_hash=hashed_password,
            role="admin",
        )

        return user
