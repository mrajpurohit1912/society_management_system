from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Type
import structlog

from app.authentication.models import UserModel
from app.authentication.strategies import (
    SignupStrategy,
    UsernamePasswordStrategy,
    EmailPasswordStrategy,
    MobileOTPStrategy,
    GoogleStrategy,
    SigninStrategy,
    UsernameSigninStrategy,
    EmailPasswordSigninStrategy,
    MobileOTPSigninStrategy,
    GoogleSigninStrategy,
)
from app.authentication.schemas import (
    UsernamePasswordSignupRequest,
    EmailPasswordSignupRequest,
    MobileOTPSignupRequest,
    GoogleSignupRequest,
    UsernameSigninRequest,
    EmailPasswordSigninRequest,
    MobileOTPSigninRequest,
    GoogleSigninRequest,
)
from app.core.cache import RedisService

logger = structlog.get_logger(__name__)

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
            logger.error("auth.signup_strategy_not_found", payload_type=type(payload).__name__)
            raise ValueError(
                f"No authentication strategy configured for request payload of type {type(payload).__name__}"
            )
        logger.debug("auth.signup_strategy_selected", strategy=type(strategy).__name__)
        return await strategy.signup(db, payload)


class LoginOrchestratorService:
    """
    Orchestrator Service for the Authentication / Signin Slice.
    Registers concrete signin strategies and executes the correct validation flow
    based on the runtime type of the request payload.
    """
    def __init__(self, redis_service: RedisService, google_client_id: str):
        """
        Initialize the orchestrator and register the active login strategies.
        """
        self._strategies: Dict[Type[BaseModel], SigninStrategy] = {}
        
        # Dynamic strategy registration (Inversion of Control)
        self.register(UsernameSigninRequest, UsernameSigninStrategy())
        self.register(EmailPasswordSigninRequest, EmailPasswordSigninStrategy())
        self.register(MobileOTPSigninRequest, MobileOTPSigninStrategy(redis_service))
        self.register(GoogleSigninRequest, GoogleSigninStrategy(google_client_id))

    def register(self, payload_type: Type[BaseModel], strategy: SigninStrategy) -> None:
        """
        Register a strategy class for a specific request model class.
        """
        self._strategies[payload_type] = strategy

    async def execute_signin(self, db: AsyncSession, payload: BaseModel) -> UserModel:
        """
        Lookup the registered strategy for the incoming payload type and run the signin.
        """
        strategy = self._strategies.get(type(payload))
        if not strategy:
            logger.error("auth.signin_strategy_not_found", payload_type=type(payload).__name__)
            raise ValueError(
                f"No signin strategy configured for request payload of type {type(payload).__name__}"
            )
        logger.debug("auth.signin_strategy_selected", strategy=type(strategy).__name__)
        return await strategy.signin(db, payload)

