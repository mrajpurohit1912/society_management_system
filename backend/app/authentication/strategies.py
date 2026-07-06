from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests
import bcrypt

from app.authentication.models import UserModel
from app.authentication.schemas import (
    UsernamePasswordSignupRequest,
    EmailPasswordSignupRequest,
    MobileOTPSignupRequest,
    GoogleSignupRequest,
)
from app.authentication.repository import UserRepository
from app.core.cache import RedisService

# Type variable bound to Pydantic schemas
T = TypeVar("T")


def hash_password(password: str) -> str:
    """
    Hash a raw password string using native bcrypt.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")



class SignupStrategy(ABC, Generic[T]):
    """
    Abstract Base Class for all Authentication / Signup strategies.
    Defines the contract for validating and registering users.
    """
    @abstractmethod
    async def signup(self, db: AsyncSession, payload: T) -> UserModel:
        """
        Execute validation and database updates for a specific signup provider.
        
        Args:
            db (AsyncSession): Scoped database session.
            payload (T): Pydantic validation request payload.
            
        Returns:
            UserModel: The newly registered user DB model.
        """
        pass


class UsernamePasswordStrategy(SignupStrategy[UsernamePasswordSignupRequest]):
    """
    Strategy for local registration using a Username and Password.
    """
    async def signup(self, db: AsyncSession, payload: UsernamePasswordSignupRequest) -> UserModel:
        repo = UserRepository(db)

        # 1. Business Check: Is the username already taken?
        existing_credential = await repo.get_credential_by_identifier(
            provider="username",
            identifier=payload.username
        )
        if existing_credential:
            raise ValueError("Username is already taken")

        # 2. Security: Hash the raw password
        hashed_password = hash_password(payload.password)

        # 3. Persistence: Write UserModel and AuthCredentialModel records via Repository
        user = await repo.create_user_with_credentials(
            first_name=payload.first_name,
            last_name=payload.last_name,
            provider="username",
            identifier=payload.username,
            password_hash=hashed_password
        )
        return user


class EmailPasswordStrategy(SignupStrategy[EmailPasswordSignupRequest]):
    """
    Strategy for local registration using an Email and Password.
    """
    async def signup(self, db: AsyncSession, payload: EmailPasswordSignupRequest) -> UserModel:
        repo = UserRepository(db)

        # 1. Check if email is already in use
        existing_credential = await repo.get_credential_by_identifier(
            provider="email",
            identifier=payload.email
        )
        if existing_credential:
            raise ValueError("Email is already registered")

        # 2. Hash password
        hashed_password = hash_password(payload.password)

        # 3. Save to DB
        user = await repo.create_user_with_credentials(
            first_name=payload.first_name,
            last_name=payload.last_name,
            provider="email",
            identifier=payload.email,
            password_hash=hashed_password
        )

        # 4. Trigger Verification Email (placeholder event)
        print(f"Triggering verification email to {payload.email}")

        return user


class MobileOTPStrategy(SignupStrategy[MobileOTPSignupRequest]):
    """
    Strategy for registration using a Mobile Number and SMS OTP.
    """
    def __init__(self, cache_service: RedisService):
        """
        Inject the Redis Cache Service to verify OTPs.
        """
        self.cache = cache_service

    async def signup(self, db: AsyncSession, payload: MobileOTPSignupRequest) -> UserModel:
        repo = UserRepository(db)

        # 1. Security check: Verify OTP matches value in Redis
        is_valid = await self.cache.verify_otp(
            phone=payload.phone_number,
            otp_code=payload.otp_code
        )
        if not is_valid:
            raise ValueError("Invalid or expired OTP code")

        # 2. Check if phone number is already registered in DB
        existing_credential = await repo.get_credential_by_identifier(
            provider="phone",
            identifier=payload.phone_number
        )
        if existing_credential:
            raise ValueError("Phone number is already registered")

        # 3. Save user profile & link phone credential (no password)
        user = await repo.create_user_with_credentials(
            first_name=payload.first_name,
            last_name=payload.last_name,
            provider="phone",
            identifier=payload.phone_number,
            password_hash=None
        )

        # 4. Invalidate the OTP in Redis immediately so it cannot be reused
        await self.cache.invalidate_otp(payload.phone_number)

        return user


class GoogleStrategy(SignupStrategy[GoogleSignupRequest]):
    """
    Strategy for registration/login using Google Social Auth.
    """
    def __init__(self, google_client_id: str):
        """
        Inject Google Client ID credentials.
        """
        self.client_id = google_client_id

    async def signup(self, db: AsyncSession, payload: GoogleSignupRequest) -> UserModel:
        repo = UserRepository(db)

        # 1. Cryptographically verify the Google ID token
        try:
            id_info = id_token.verify_oauth2_token(
                payload.google_id_token,
                requests.Request(),
                self.client_id
            )
        except Exception:
            raise ValueError("Invalid Google OAuth token")

        # 2. Extract user details from Google token claims
        google_sub = id_info["sub"]
        email = id_info.get("email")
        first_name = id_info.get("given_name", "Google")
        last_name = id_info.get("family_name", "User")

        # 3. Check if Google identity already linked to a user in our DB
        existing_credential = await repo.get_credential_by_identifier(
            provider="google",
            identifier=google_sub
        )
        if existing_credential:
            # User is already signed up with Google. Return existing user.
            return await repo.get_user_by_id(existing_credential.user_id)

        # 4. Save new user linked to Google credential
        user = await repo.create_user_with_credentials(
            first_name=first_name,
            last_name=last_name,
            provider="google",
            identifier=google_sub,
            password_hash=None
        )
        return user
