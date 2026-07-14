from unittest.mock import MagicMock, AsyncMock
import pytest
from pydantic import BaseModel

from app.authentication.services import AuthOrchestratorService, LoginOrchestratorService
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
