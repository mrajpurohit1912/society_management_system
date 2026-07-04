from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Type

from app.authentication.models import UserModel
from app.authentication.strategies import (
    SignupStrategy,
    UsernamePasswordStrategy,
    EmailPasswordStrategy,
    MobileOTPStrategy,
    GoogleStrategy,
)
from app.authentication.schemas import (
    UsernamePasswordSignupRequest,
    EmailPasswordSignupRequest,
    MobileOTPSignupRequest,
    GoogleSignupRequest,
)
from app.core.cache import RedisService

class AuthOrchestratorService:
    """
    Orchestrator Service (Coordinator / Registry Pattern) for the Authentication Slice.
    Registers concrete strategies and executes the correct registration flow 
    based on the runtime type of the validation schema payload.
    """
    def __init__(self, redis_service: RedisService, google_client_id: str):
        """
        Initialize the orchestrator and register the active signup strategies.
        
        Args:
            redis_service (RedisService): Global Redis client service.
            google_client_id (str): Google Client ID for OAuth token checks.
        """
        self._strategies: Dict[Type[BaseModel], SignupStrategy] = {}
        
        # Dynamic strategy registration (Inversion of Control)
        self.register(UsernamePasswordSignupRequest, UsernamePasswordStrategy())
        self.register(EmailPasswordSignupRequest, EmailPasswordStrategy())
        self.register(MobileOTPSignupRequest, MobileOTPStrategy(redis_service))
        self.register(GoogleSignupRequest, GoogleStrategy(google_client_id))

    def register(self, payload_type: Type[BaseModel], strategy: SignupStrategy) -> None:
        """
        Register a strategy class for a specific request model class.
        """
        self._strategies[payload_type] = strategy

    async def execute_signup(self, db: AsyncSession, payload: BaseModel) -> UserModel:
        """
        Lookup the registered strategy for the incoming payload type and run the signup.
        
        Args:
            db (AsyncSession): Active database session.
            payload (BaseModel): Incoming validated request schema payload.
            
        Returns:
            UserModel: The registered user database entity.
            
        Raises:
            ValueError: If no strategy matches the request payload.
        """
        strategy = self._strategies.get(type(payload))
        if not strategy:
            raise ValueError(
                f"No authentication strategy configured for request payload of type {type(payload).__name__}"
            )
        return await strategy.signup(db, payload)
