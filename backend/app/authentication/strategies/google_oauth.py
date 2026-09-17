from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests
import structlog

from app.authentication.models import UserModel
from app.authentication.schemas import (
    GoogleSignupRequest,
    GoogleSigninRequest,
)
from app.authentication.repository import UserRepository
from app.authentication.strategies.base import SignupStrategy, SigninStrategy

logger = structlog.get_logger(__name__)


class GoogleStrategy(SignupStrategy[GoogleSignupRequest]):
    """
    Strategy for registration/login using Google Social Auth.
    """

    def __init__(self, google_client_id: str):
        self.client_id = google_client_id

    async def signup(self, db: AsyncSession, payload: GoogleSignupRequest) -> UserModel:
        repo = UserRepository(db)
        logger.info("strategy.google_signup_attempt")

        # 1. Cryptographically verify the Google ID token
        try:
            id_info = id_token.verify_oauth2_token(
                payload.google_id_token,
                requests.Request(),
                self.client_id,
            )
        except Exception as e:
            logger.warning("strategy.google_signup_invalid_token", error=str(e))
            raise ValueError("Invalid Google OAuth token")

        # 2. Extract user details from Google token claims
        google_sub = id_info["sub"]
        first_name = id_info.get("given_name", "Google")
        last_name = id_info.get("family_name", "User")

        # 3. Check if Google identity already linked to a user in our DB
        existing_credential = await repo.get_credential_by_identifier(
            provider="google",
            identifier=google_sub,
        )
        if existing_credential:
            logger.info("strategy.google_signup_existing_user", user_id=str(existing_credential.user_id))
            return await repo.get_user_by_id(existing_credential.user_id)

        # 4. Save new user linked to Google credential
        user = await repo.create_user_with_credentials(
            first_name=first_name,
            last_name=last_name,
            provider="google",
            identifier=google_sub,
            password_hash=None,
        )
        return user


class GoogleSigninStrategy(SigninStrategy[GoogleSigninRequest]):
    """
    Strategy for authentication/login using Google Social Auth.
    """

    def __init__(self, google_client_id: str):
        self.client_id = google_client_id

    async def signin(self, db: AsyncSession, payload: GoogleSigninRequest) -> UserModel:
        logger.info("strategy.google_signin_attempt")
        try:
            id_info = id_token.verify_oauth2_token(
                payload.google_id_token,
                requests.Request(),
                self.client_id,
            )
        except Exception as e:
            logger.warning("strategy.google_signin_invalid_token", error=str(e))
            raise ValueError("Invalid Google OAuth token")

        google_sub = id_info["sub"]
        repo = UserRepository(db)
        result = await repo.get_user_by_credential(provider="google", identifier=google_sub)
        if not result:
            logger.warning("strategy.google_signin_not_found", google_sub=google_sub)
            raise ValueError("Google account is not registered. Please sign up first.")

        user, _ = result
        return user
