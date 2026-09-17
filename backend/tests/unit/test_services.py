import uuid
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from pydantic import BaseModel

from app.authentication.services import AuthOrchestratorService, LoginOrchestratorService, AuthFlowService
from app.authentication.schemas import (
    ResidentSignupRequest,
    VerifyEmailRequest,
    AdminActivateRequest,
    UnifiedLoginRequest,
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
from app.authentication.strategies import (
    UsernamePasswordStrategy,
    EmailPasswordStrategy,
    MobileOTPStrategy,
    GoogleStrategy,
    AdminSignupStrategy,
    UsernameSigninStrategy,
    EmailPasswordSigninStrategy,
    MobileOTPSigninStrategy,
    GoogleSigninStrategy,
)


@pytest.fixture
def mock_redis_service():
    """Provides a mocked RedisService instance so that tests do not establish physical connections."""
    return MagicMock()


@pytest.fixture
def google_client_id():
    """Provides a dummy Client ID for testing Google OAuth Strategy registration."""
    return "test-google-client-id"


def test_auth_orchestrator_initialization(mock_redis_service, google_client_id):
    """
    Test that AuthOrchestratorService initializes and registers the correct concrete signup strategies.
    """
    orchestrator = AuthOrchestratorService(mock_redis_service, google_client_id)
    
    assert len(orchestrator._strategies) == 5
    assert isinstance(orchestrator._strategies[UsernamePasswordSignupRequest], UsernamePasswordStrategy)
    assert isinstance(orchestrator._strategies[EmailPasswordSignupRequest], EmailPasswordStrategy)
    assert isinstance(orchestrator._strategies[MobileOTPSignupRequest], MobileOTPStrategy)
    assert isinstance(orchestrator._strategies[GoogleSignupRequest], GoogleStrategy)
    assert isinstance(orchestrator._strategies[AdminSignupRequest], AdminSignupStrategy)


@pytest.mark.asyncio
async def test_auth_orchestrator_execute_signup_success(mock_redis_service, google_client_id):
    """
    Test that execute_signup correctly resolves the registered strategy, invokes its signup method,
    and returns the registered user database entity.
    """
    orchestrator = AuthOrchestratorService(mock_redis_service, google_client_id)
    
    mock_db = AsyncMock()
    payload = UsernamePasswordSignupRequest(
        first_name="John",
        last_name="Doe",
        username="testuser",
        password="password123"
    )
    
    # Mock the strategy registration to isolate service orchestrator logic
    mock_strategy = AsyncMock()
    mock_user = MagicMock()
    mock_strategy.signup.return_value = mock_user
    orchestrator._strategies[UsernamePasswordSignupRequest] = mock_strategy
    
    result = await orchestrator.execute_signup(mock_db, payload)
    
    mock_strategy.signup.assert_called_once_with(mock_db, payload)
    assert result == mock_user


@pytest.mark.asyncio
async def test_auth_orchestrator_execute_signup_unregistered(mock_redis_service, google_client_id):
    """
    Test that execute_signup raises a ValueError when invoked with an unregistered request schema.
    """
    orchestrator = AuthOrchestratorService(mock_redis_service, google_client_id)
    mock_db = AsyncMock()
    
    # Create a mock schema that is not registered with the orchestrator
    class UnregisteredSignupRequest(BaseModel):
        first_name: str
        last_name: str

    payload = UnregisteredSignupRequest(first_name="Jane", last_name="Doe")
    
    with pytest.raises(ValueError) as exc_info:
        await orchestrator.execute_signup(mock_db, payload)
        
    assert "No authentication strategy configured for request payload of type UnregisteredSignupRequest" in str(exc_info.value)


def test_login_orchestrator_initialization(mock_redis_service, google_client_id):
    """
    Test that LoginOrchestratorService initializes and registers the correct concrete login strategies.
    """
    orchestrator = LoginOrchestratorService(mock_redis_service, google_client_id)
    
    assert len(orchestrator._strategies) == 4
    assert isinstance(orchestrator._strategies[UsernameSigninRequest], UsernameSigninStrategy)
    assert isinstance(orchestrator._strategies[EmailPasswordSigninRequest], EmailPasswordSigninStrategy)
    assert isinstance(orchestrator._strategies[MobileOTPSigninRequest], MobileOTPSigninStrategy)
    assert isinstance(orchestrator._strategies[GoogleSigninRequest], GoogleSigninStrategy)


@pytest.mark.asyncio
async def test_login_orchestrator_execute_signin_success(mock_redis_service, google_client_id):
    """
    Test that execute_signin correctly resolves the registered strategy, invokes its signin method,
    and returns the authenticated user database entity.
    """
    orchestrator = LoginOrchestratorService(mock_redis_service, google_client_id)
    
    mock_db = AsyncMock()
    payload = UsernameSigninRequest(
        username="testuser",
        password="password123"
    )
    
    # Mock the strategy registration to isolate service orchestrator logic
    mock_strategy = AsyncMock()
    mock_user = MagicMock()
    mock_strategy.signin.return_value = mock_user
    orchestrator._strategies[UsernameSigninRequest] = mock_strategy
    
    result = await orchestrator.execute_signin(mock_db, payload)
    
    mock_strategy.signin.assert_called_once_with(mock_db, payload)
    assert result == mock_user


@pytest.mark.asyncio
async def test_login_orchestrator_execute_signin_unregistered(mock_redis_service, google_client_id):
    """
    Test that execute_signin raises a ValueError when invoked with an unregistered request schema.
    """
    orchestrator = LoginOrchestratorService(mock_redis_service, google_client_id)
    mock_db = AsyncMock()
    
    # Create a mock schema that is not registered with the orchestrator
    class UnregisteredSigninRequest(BaseModel):
        username: str
        password: str

    payload = UnregisteredSigninRequest(username="testuser", password="password123")
    
    with pytest.raises(ValueError) as exc_info:
        await orchestrator.execute_signin(mock_db, payload)
        
    assert "No signin strategy configured for request payload of type UnregisteredSigninRequest" in str(exc_info.value)


# ==============================================================================
# AuthFlowService Unit Tests
# ==============================================================================

@pytest.mark.asyncio
@patch("app.core.email_service.EmailService.send_resident_verification_email")
@patch("app.authentication.services.UserRepository")
async def test_resident_signup_success(mock_user_repo_cls, mock_email):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_credential_by_identifier.return_value = None
    mock_user = MagicMock(user_id=uuid.uuid4(), email_verified=False)
    mock_repo.create_user.return_value = mock_user
    mock_user_repo_cls.return_value = mock_repo

    payload = ResidentSignupRequest(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        password="securepassword123"
    )

    result = await AuthFlowService.resident_signup(mock_db, payload)
    assert result == mock_user
    mock_repo.get_credential_by_identifier.assert_called_once_with("email", "jane@example.com")
    mock_repo.create_user.assert_called_once()
    mock_repo.add_credential.assert_called_once()
    mock_repo.create_activation_token.assert_called_once()
    mock_email.assert_called_once()


@pytest.mark.asyncio
@patch("app.authentication.services.UserRepository")
async def test_resident_signup_email_exists(mock_user_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_credential_by_identifier.return_value = MagicMock()
    mock_user_repo_cls.return_value = mock_repo

    payload = ResidentSignupRequest(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        password="securepassword123"
    )

    with pytest.raises(ValueError) as exc:
        await AuthFlowService.resident_signup(mock_db, payload)
    assert "already exists" in str(exc.value)


@pytest.mark.asyncio
@patch("app.authentication.services.UserRepository")
async def test_verify_email_success(mock_user_repo_cls):
    from datetime import datetime, timezone, timedelta
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    u_id = uuid.uuid4()
    mock_token = MagicMock(user_id=u_id, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    mock_repo.get_valid_activation_token.return_value = mock_token
    mock_user = MagicMock(user_id=u_id, email_verified=False)
    mock_repo.get_user_by_id.return_value = mock_user
    mock_user_repo_cls.return_value = mock_repo

    payload = VerifyEmailRequest(token="valid_token_123")
    result = await AuthFlowService.verify_email(mock_db, payload)
    assert result == mock_user
    mock_repo.update_user.assert_called_once_with(mock_user, email_verified=True, status="email_verified")
    mock_repo.mark_token_used.assert_called_once_with(mock_token)


@pytest.mark.asyncio
@patch("app.authentication.services.UserRepository")
async def test_activate_admin_success(mock_user_repo_cls):
    from datetime import datetime, timezone, timedelta
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    u_id = uuid.uuid4()
    mock_token = MagicMock(user_id=u_id, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    mock_repo.get_valid_activation_token.return_value = mock_token
    mock_user = MagicMock(user_id=u_id)
    mock_repo.get_user_by_id.return_value = mock_user
    mock_cred = MagicMock()
    mock_repo.get_credential_by_user_id.return_value = mock_cred
    mock_user_repo_cls.return_value = mock_repo

    payload = AdminActivateRequest(token="admin_token_123", password="new_password_123")
    result = await AuthFlowService.activate_admin(mock_db, payload)
    assert result == mock_user
    mock_repo.update_credential_password.assert_called_once()
    mock_repo.update_user.assert_called_once_with(mock_user, status="active")
    mock_repo.mark_token_used.assert_called_once_with(mock_token)

