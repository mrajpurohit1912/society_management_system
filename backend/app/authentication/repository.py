import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.authentication.models import UserModel, AuthCredentialModel, RefreshTokenModel, ActivationTokenModel

class UserRepository:
    """
    Data Access Layer (Repository Pattern) for Authentication Service.
    Encapsulates all DB operations using SQLAlchemy 2.0 Async Session.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_user_exist(self, user_id: uuid.UUID) -> Optional[UserModel]:
        """Fetch user by primary key, pre-loading credentials."""
        query = (
            select(UserModel)
            .where(UserModel.user_id == user_id)
            .options(selectinload(UserModel.credentials))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_credential_by_identifier(self, provider: str, identifier: str) -> Optional[AuthCredentialModel]:
        """Fetch a credential to check if a username/email/phone is already registered."""
        query = select(AuthCredentialModel).where(
            AuthCredentialModel.provider == provider,
            AuthCredentialModel.identifier == identifier
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_credential(
        self, provider: str, identifier: str
    ) -> Optional[tuple[UserModel, AuthCredentialModel]]:
        """Fetch user and credential in one query for signin verification."""
        query = (
            select(UserModel, AuthCredentialModel)
            .join(AuthCredentialModel, UserModel.user_id == AuthCredentialModel.user_id)
            .where(
                AuthCredentialModel.provider == provider,
                AuthCredentialModel.identifier == identifier
            )
        )
        result = await self.db.execute(query)
        row = result.first()
        if row:
            # SQLAlchemy returns a tuple (UserModel, AuthCredentialModel)
            return row[0], row[1]
        return None

    async def create_user_with_credentials(
        self,
        first_name: str,
        last_name: str,
        provider: str,
        identifier: str,
        password_hash: Optional[str] = None,
        role: str = "member"
    ) -> UserModel:
        """Atomically create user and credential record inside the transaction."""
        # 1. Create Core User
        user = UserModel(
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        self.db.add(user)
        await self.db.flush()

        # 2. Link Credential Identity
        credential = AuthCredentialModel(
            user_id=user.user_id,
            provider=provider,
            identifier=identifier,
            password_hash=password_hash
        )
        self.db.add(credential)
        await self.db.flush()

        return user

    async def add_refresh_token(self, user_id: uuid.UUID | str, token_hash: str, expires_at: datetime) -> RefreshTokenModel:
        """Register a new active refresh token session for a user."""
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        token = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_user_credentials(self, user_id: uuid.UUID) -> list[AuthCredentialModel]:
        """Fetch all credentials associated with a user ID."""
        query = select(AuthCredentialModel).where(AuthCredentialModel.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserModel]:
        """Fetch a user record by primary key."""
        query = select(UserModel).where(UserModel.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        first_name: str,
        last_name: str,
        role: str = "resident",
        status: str = "registered",
        email_verified: bool = False,
    ) -> UserModel:
        """Create a new user with status and verification flags."""
        user = UserModel(
            first_name=first_name,
            last_name=last_name,
            role=role,
            status=status,
            email_verified=email_verified,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def add_credential(
        self,
        user_id: uuid.UUID,
        provider: str,
        identifier: str,
        password_hash: Optional[str] = None,
    ) -> AuthCredentialModel:
        """Attach a new credential identity to a user."""
        credential = AuthCredentialModel(
            user_id=user_id,
            provider=provider,
            identifier=identifier,
            password_hash=password_hash,
        )
        self.db.add(credential)
        await self.db.flush()
        return credential

    async def get_credential_by_user_id(
        self, user_id: uuid.UUID, provider: Optional[str] = None
    ) -> Optional[AuthCredentialModel]:
        """Fetch credential by user ID and optional provider."""
        query = select(AuthCredentialModel).where(AuthCredentialModel.user_id == user_id)
        if provider:
            query = query.where(AuthCredentialModel.provider == provider)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_activation_token(
        self,
        user_id: uuid.UUID,
        token: str,
        token_type: str,
        expires_at: datetime,
    ) -> ActivationTokenModel:
        """Create and store an activation or verification token."""
        activation_token = ActivationTokenModel(
            user_id=user_id,
            token=token,
            type=token_type,
            expires_at=expires_at,
        )
        self.db.add(activation_token)
        await self.db.flush()
        return activation_token

    async def get_valid_activation_token(
        self, token: str, token_type: str
    ) -> Optional[ActivationTokenModel]:
        """Fetch an unused activation or verification token matching type."""
        query = select(ActivationTokenModel).where(
            ActivationTokenModel.token == token,
            ActivationTokenModel.type == token_type,
            ActivationTokenModel.used_at.is_(None),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def mark_token_used(self, token_record: ActivationTokenModel) -> None:
        """Mark an activation token as consumed."""
        token_record.used_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def update_user(
        self,
        user: UserModel,
        status: Optional[str] = None,
        email_verified: Optional[bool] = None,
    ) -> UserModel:
        """Update user account status and verification flags."""
        if status is not None:
            user.status = status
        if email_verified is not None:
            user.email_verified = email_verified
        await self.db.flush()
        return user

    async def update_credential_password(
        self, credential: AuthCredentialModel, password_hash: str
    ) -> AuthCredentialModel:
        """Update password hash on an existing credential."""
        credential.password_hash = password_hash
        await self.db.flush()
        return credential