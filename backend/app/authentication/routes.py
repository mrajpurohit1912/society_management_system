import os
import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.cache import RedisService
from app.core.logging_context import set_logging_context
from app.authentication.schemas import (
    UsernamePasswordSignupRequest,
    EmailPasswordSignupRequest,
    MobileOTPSignupRequest,
    GoogleSignupRequest,
    UsernameSigninRequest,
    EmailPasswordSigninRequest,
    MobileOTPSigninRequest,
    GoogleSigninRequest,
    AdminSignupRequest,
)
from app.authentication.services import AuthOrchestratorService, LoginOrchestratorService
from app.authentication.security import TokenService
from app.authentication.repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = structlog.get_logger(__name__)

# Core Services Instantiation
redis_service = RedisService()
google_client_id = os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id")
orchestrator = AuthOrchestratorService(redis_service, google_client_id)
login_orchestrator = LoginOrchestratorService(redis_service, google_client_id)


async def get_orchestrator() -> AuthOrchestratorService:
    """Dependency to provide the global authentication orchestrator service."""
    return orchestrator


async def get_login_orchestrator() -> LoginOrchestratorService:
    """Dependency to provide the global authentication login orchestrator service."""
    return login_orchestrator



async def _handle_signup_and_issue_tokens(
    payload,
    response: Response,
    db: AsyncSession,
    auth_service: AuthOrchestratorService
) -> dict:
    """
    Common helper executing the registration strategy inside an atomic database 
    transaction and configuring session cookies outside it.
    """
    strategy_name = type(payload).__name__
    logger.info("auth.signup_started", strategy=strategy_name)
    try:
        # Atomic Transaction Block
        # If any db query or logic inside fails, SQLAlchemy rolls back automatically
        async with db.begin():
            user = await auth_service.execute_signup(db, payload)
            user_id_str = str(user.user_id)
            set_logging_context(user_id=user_id_str)
            
            # Generate refresh token details
            raw_refresh, refresh_hash, expires_at = TokenService.create_refresh_token(user_id_str)
            
            # Save refresh token hash in DB
            repo = UserRepository(db)
            await repo.add_refresh_token(
                user_id=user.user_id,
                token_hash=refresh_hash,
                expires_at=expires_at
            )

        # Generate access token
        access_token = TokenService.create_access_token(user_id_str, user.role)

        # Set secure HttpOnly cookie for refresh token (XSS & CSRF mitigation)
        response.set_cookie(
            key="refresh_token",
            value=raw_refresh,
            httponly=True,
            secure=True,
            samesite="strict",
            expires=expires_at
        )

        logger.info("auth.signup_success", strategy=strategy_name, user_id=user_id_str)
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError as e:
        logger.warning("auth.signup_failed", strategy=strategy_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def _handle_login_and_issue_tokens(
    payload,
    response: Response,
    db: AsyncSession,
    login_service: LoginOrchestratorService
) -> dict:
    """
    Common helper executing the login strategy inside an atomic database 
    transaction and configuring session cookies outside it.
    """
    strategy_name = type(payload).__name__
    logger.info("auth.login_started", strategy=strategy_name)
    try:
        # Atomic Transaction Block
        async with db.begin():
            user = await login_service.execute_signin(db, payload)
            user_id_str = str(user.user_id)
            set_logging_context(user_id=user_id_str)
            
            # Generate refresh token details
            raw_refresh, refresh_hash, expires_at = TokenService.create_refresh_token(user_id_str)
            
            # Save refresh token hash in DB
            repo = UserRepository(db)
            await repo.add_refresh_token(
                user_id=user.user_id,
                token_hash=refresh_hash,
                expires_at=expires_at
            )

        # Generate access token
        access_token = TokenService.create_access_token(user_id_str, user.role)

        # Set secure HttpOnly cookie for refresh token (XSS & CSRF mitigation)
        response.set_cookie(
            key="refresh_token",
            value=raw_refresh,
            httponly=True,
            secure=True,
            samesite="strict",
            expires=expires_at
        )

        logger.info("auth.login_success", strategy=strategy_name, user_id=user_id_str)
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError as e:
        logger.warning("auth.login_failed", strategy=strategy_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



@router.post("/signup/username", status_code=status.HTTP_201_CREATED)
async def signup_username(
    payload: UsernamePasswordSignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthOrchestratorService = Depends(get_orchestrator)
):
    """
    Register a user using a unique Username and Password.
    """
    return await _handle_signup_and_issue_tokens(payload, response, db, auth_service)


@router.post("/signup/email", status_code=status.HTTP_201_CREATED)
async def signup_email(
    payload: EmailPasswordSignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthOrchestratorService = Depends(get_orchestrator)
):
    """
    Register a user using an Email and Password.
    """
    return await _handle_signup_and_issue_tokens(payload, response, db, auth_service)


@router.post("/signup/otp", status_code=status.HTTP_201_CREATED)
async def signup_otp(
    payload: MobileOTPSignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthOrchestratorService = Depends(get_orchestrator)
):
    """
    Register a user by verifying a one-time passcode (OTP) sent to their mobile number.
    """
    return await _handle_signup_and_issue_tokens(payload, response, db, auth_service)


@router.post("/signup/google", status_code=status.HTTP_201_CREATED)
async def signup_google(
    payload: GoogleSignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthOrchestratorService = Depends(get_orchestrator)
):
    """
    Register or log in a user using their Google OAuth ID token.
    """
    return await _handle_signup_and_issue_tokens(payload, response, db, auth_service)


@router.post("/signup/admin", status_code=status.HTTP_201_CREATED)
async def signup_admin(
    payload: AdminSignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthOrchestratorService = Depends(get_orchestrator)
):
    """
    Register an administrative user using an Email, Password, and the Admin Setup Secret.
    """
    return await _handle_signup_and_issue_tokens(payload, response, db, auth_service)



@router.post("/login/username")
async def login_username(
    payload: UsernameSigninRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    login_service: LoginOrchestratorService = Depends(get_login_orchestrator)
):
    """
    Authenticate a user using their Username and Password.
    """
    return await _handle_login_and_issue_tokens(payload, response, db, login_service)


@router.post("/login/email")
async def login_email(
    payload: EmailPasswordSigninRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    login_service: LoginOrchestratorService = Depends(get_login_orchestrator)
):
    """
    Authenticate a user using their Email and Password.
    """
    return await _handle_login_and_issue_tokens(payload, response, db, login_service)


@router.post("/login/otp")
async def login_otp(
    payload: MobileOTPSigninRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    login_service: LoginOrchestratorService = Depends(get_login_orchestrator)
):
    """
    Authenticate a user by verifying a one-time passcode (OTP) sent to their mobile number.
    """
    return await _handle_login_and_issue_tokens(payload, response, db, login_service)


@router.post("/login/google")
async def login_google(
    payload: GoogleSigninRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    login_service: LoginOrchestratorService = Depends(get_login_orchestrator)
):
    """
    Authenticate a user using their Google OAuth ID token.
    """
    return await _handle_login_and_issue_tokens(payload, response, db, login_service)

