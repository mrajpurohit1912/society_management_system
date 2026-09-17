from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

from app.authentication.models import UserModel

T = TypeVar("T")


class SignupStrategy(ABC, Generic[T]):
    """
    Abstract Base Class for all Authentication / Signup strategies.
    Defines the contract for validating and registering users.
    """

    @abstractmethod
    async def signup(self, db: AsyncSession, payload: T) -> UserModel:
        """
        Execute validation and database updates for a specific signup provider.
        """
        pass


class SigninStrategy(ABC, Generic[T]):
    """
    Abstract Base Class for all Authentication / Signin strategies.
    Defines the contract for validating and authenticating users.
    """

    @abstractmethod
    async def signin(self, db: AsyncSession, payload: T) -> UserModel:
        """
        Execute validation and database updates for a specific signin provider.
        """
        pass
