from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.authentication.models import UserModel
from app.authentication.schemas import (
    UsernamePasswordSignupRequest,
    UsernameSigninRequest,
)
from app.authentication.repository import UserRepository
from app.authentication.security import PasswordHasher
from app.authentication.strategies.base import SignupStrategy, SigninStrategy

logger = structlog.get_logger(__name__)


class UsernamePasswordStrategy(SignupStrategy[UsernamePasswordSignupRequest]):
    """
    Strategy for local registration using a Username and Password.
    """

    async def signup(self, db: AsyncSession, payload: UsernamePasswordSignupRequest) -> UserModel:
        repo = UserRepository(db)

        # 1. Business Check: Is the username already taken?
        logger.info("strategy.username_signup_attempt", username=payload.username)
        existing_credential = await repo.get_credential_by_identifier(
            provider="username",
            identifier=payload.username,
        )
        if existing_credential:
            logger.warning("strategy.username_signup_taken", username=payload.username)
            raise ValueError("Username is already taken")

        # 2. Security: Hash the raw password via central PasswordHasher
        hashed_password = PasswordHasher.hash_password(payload.password)

        # 3. Persistence: Write UserModel and AuthCredentialModel records via Repository
        user = await repo.create_user_with_credentials(
            first_name=payload.first_name,
            last_name=payload.last_name,
            provider="username",
            identifier=payload.username,
            password_hash=hashed_password,
        )
        return user


class UsernameSigninStrategy(SigninStrategy[UsernameSigninRequest]):
    """
    Strategy for local authentication using a Username and Password.
    """

    async def signin(self, db: AsyncSession, payload: UsernameSigninRequest) -> UserModel:
        repo = UserRepository(db)
        logger.info("strategy.username_signin_attempt", username=payload.username)

        result = await repo.get_user_by_credential(provider="username", identifier=payload.username)
        if not result:
            logger.warning("strategy.username_signin_failed_missing_user", username=payload.username)
            raise ValueError("Invalid username or password")

        user, credential = result
        if not credential.password_hash:
            logger.warning("strategy.username_signin_failed_missing_hash", username=payload.username)
            raise ValueError("Invalid username or password")

        is_valid = PasswordHasher.verify_password(payload.password, credential.password_hash)
        if not is_valid:
            logger.warning("strategy.username_signin_failed_bad_password", username=payload.username)
            raise ValueError("Invalid username or password")

        return user
