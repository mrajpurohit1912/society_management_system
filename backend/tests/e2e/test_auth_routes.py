import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db_session
from app.authentication.routes import get_orchestrator, get_login_orchestrator


@pytest.fixture
def mock_db():
    """Mock the AsyncSession and database transaction context manager."""
    # We use AsyncMock for the session, but override begin with a MagicMock
    # so that calling db.begin() returns a transaction mock with __aenter__ and __aexit__.
    from sqlalchemy.ext.asyncio import AsyncSession
    session = AsyncMock(spec=AsyncSession)
    session.begin = MagicMock()
    session.begin.return_value.__aenter__ = AsyncMock()
    session.begin.return_value.__aexit__ = AsyncMock(return_value=False)
    return session


@pytest.fixture
def mock_auth_service():
    """Mock the AuthOrchestratorService."""
    return AsyncMock()


@pytest.fixture
def mock_login_service():
    """Mock the LoginOrchestratorService."""
    return AsyncMock()


@pytest.fixture
def test_client(mock_db, mock_auth_service, mock_login_service):
    """
    Provides a FastAPI TestClient with dependency overrides configured for testing.
    Dependency overrides are cleared automatically during teardown.
    """
    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_orchestrator] = lambda: mock_auth_service
    app.dependency_overrides[get_login_orchestrator] = lambda: mock_login_service
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    """Provides a mocked user entity."""
    user = MagicMock()
    user.user_id = uuid.uuid4()
    user.first_name = "John"
    user.last_name = "Doe"
    user.role = "member"
    return user


# ==============================================================================
# Signup Endpoint Tests
# ==============================================================================

@patch("app.authentication.routes.UserRepository")
def test_signup_username_success(mock_repo_cls, test_client, mock_auth_service, mock_user):
    """
    Test successful username signup returns a 201 status code, an access token,
    and sets a secure HttpOnly cookie containing the refresh token.
    """
    # Arrange
    mock_auth_service.execute_signup.return_value = mock_user
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "username": "john_doe",
        "password": "secure_password_123"
    }
    
    # Act
    response = test_client.post("/api/v1/auth/signup/username", json=payload)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Check that the HttpOnly refresh token cookie is set
    assert "refresh_token" in response.cookies
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie_header
    assert "secure" in set_cookie_header.lower()
    assert "samesite=strict" in set_cookie_header.lower()
    
    mock_auth_service.execute_signup.assert_called_once()
    mock_repo.add_refresh_token.assert_called_once()


@patch("app.authentication.routes.UserRepository")
def test_signup_username_taken_error(mock_repo_cls, test_client, mock_auth_service):
    """
    Test that if the registration strategy raises a ValueError (e.g. username taken),
    the endpoint returns 400 Bad Request.
    """
    # Arrange
    mock_auth_service.execute_signup.side_effect = ValueError("Username is already taken")
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "username": "john_taken",
        "password": "secure_password_123"
    }
    
    # Act
    response = test_client.post("/api/v1/auth/signup/username", json=payload)
    
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Username is already taken"
    mock_repo.add_refresh_token.assert_not_called()


def test_signup_username_validation_error(test_client):
    """
    Test that passing invalid request parameters (e.g. password too short)
    returns a 422 Unprocessable Entity status code.
    """
    # Act: password length of 4 is invalid (min_length=8)
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "username": "john_doe",
        "password": "123"
    }
    response = test_client.post("/api/v1/auth/signup/username", json=payload)
    
    # Assert
    assert response.status_code == 422


@patch("app.authentication.routes.UserRepository")
def test_signup_email_success(mock_repo_cls, test_client, mock_auth_service, mock_user):
    """Test successful email signup."""
    mock_auth_service.execute_signup.return_value = mock_user
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "password": "secure_password_123"
    }
    
    response = test_client.post("/api/v1/auth/signup/email", json=payload)
    
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert "refresh_token" in response.cookies


@patch("app.authentication.routes.UserRepository")
def test_signup_otp_success(mock_repo_cls, test_client, mock_auth_service, mock_user):
    """Test successful OTP signup."""
    mock_auth_service.execute_signup.return_value = mock_user
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890",
        "otp_code": "123456"
    }
    
    response = test_client.post("/api/v1/auth/signup/otp", json=payload)
    
    assert response.status_code == 201
    assert "access_token" in response.json()


@patch("app.authentication.routes.UserRepository")
def test_signup_google_success(mock_repo_cls, test_client, mock_auth_service, mock_user):
    """Test successful Google signup."""
    mock_auth_service.execute_signup.return_value = mock_user
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    
    payload = {
        "google_id_token": "google-dummy-jwt-token"
    }
    
    response = test_client.post("/api/v1/auth/signup/google", json=payload)
    
    assert response.status_code == 201
    assert "access_token" in response.json()


# ==============================================================================
# Login Endpoint Tests
# ==============================================================================

@patch("app.authentication.routes.UserRepository")
def test_login_username_success(mock_repo_cls, test_client, mock_login_service, mock_user):
    """
    Test successful username login returns 200 OK, access token, and sets refresh token cookie.
    """
    # Arrange
    mock_login_service.execute_signin.return_value = mock_user
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    
    payload = {
        "username": "john_doe",
        "password": "secure_password_123"
    }
    
    # Act
    response = test_client.post("/api/v1/auth/login/username", json=payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in response.cookies
    mock_login_service.execute_signin.assert_called_once()
    mock_repo.add_refresh_token.assert_called_once()


@patch("app.authentication.routes.UserRepository")
def test_login_username_failure(mock_repo_cls, test_client, mock_login_service):
    """
    Test that invalid credentials (ValueError raised) return 400 Bad Request.
    """
    # Arrange
    mock_login_service.execute_signin.side_effect = ValueError("Invalid username or password")
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    
    payload = {
        "username": "john_wrong",
        "password": "wrong_password"
    }
    
    # Act
    response = test_client.post("/api/v1/auth/login/username", json=payload)
    
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid username or password"
    mock_repo.add_refresh_token.assert_not_called()


@patch("app.authentication.routes.UserRepository")
def test_login_email_success(mock_repo_cls, test_client, mock_login_service, mock_user):
    """Test successful email login."""
    mock_login_service.execute_signin.return_value = mock_user
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    
    payload = {
        "email": "john@example.com",
        "password": "secure_password_123"
    }
    
    response = test_client.post("/api/v1/auth/login/email", json=payload)
    
    assert response.status_code == 200
    assert "access_token" in response.json()


@patch("app.authentication.routes.UserRepository")
def test_login_otp_success(mock_repo_cls, test_client, mock_login_service, mock_user):
    """Test successful mobile OTP login."""
    mock_login_service.execute_signin.return_value = mock_user
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    
    payload = {
        "phone_number": "+1234567890",
        "otp_code": "123456"
    }
    
    response = test_client.post("/api/v1/auth/login/otp", json=payload)
    
    assert response.status_code == 200
    assert "access_token" in response.json()


@patch("app.authentication.routes.UserRepository")
def test_login_google_success(mock_repo_cls, test_client, mock_login_service, mock_user):
    """Test successful Google login."""
    mock_login_service.execute_signin.return_value = mock_user
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    
    payload = {
        "google_id_token": "google-dummy-jwt-token"
    }
    
    response = test_client.post("/api/v1/auth/login/google", json=payload)
    
    assert response.status_code == 200
    assert "access_token" in response.json()
