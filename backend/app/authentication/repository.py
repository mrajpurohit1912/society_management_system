import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.authentication.models import UserModel, AuthCredentialModel, RefreshTokenModel

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

    async def create_user_with_credentials(
        self,
        first_name: str,
        last_name: str,
        provider: str,
        identifier: str,
        password_hash: Optional[str] = None
    ) -> UserModel:
        """Atomically create user and credential record inside the transaction."""
        # 1. Create Core User
        user = UserModel(
            first_name=first_name,
            last_name=last_name
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

    async def add_refresh_token(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshTokenModel:
        """Register a new active refresh token session for a user."""
        token = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(token)
        await self.db.flush()
        return token