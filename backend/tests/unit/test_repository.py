import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from app.authentication.repository import UserRepository
from app.authentication.models import UserModel, AuthCredentialModel, RefreshTokenModel


@pytest.fixture
def mock_db_session():
    """Provides a mocked SQLAlchemy AsyncSession."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_db_session):
    """Provides an instance of UserRepository bound to the mock session."""
    return UserRepository(mock_db_session)


@pytest.mark.asyncio
async def test_check_user_exist_returns_user(repo, mock_db_session):
    """
    Test that check_user_exist correctly executes a select query and returns the user model.
    """
    user_id = uuid.uuid4()
    mock_user = UserModel(user_id=user_id, first_name="John", last_name="Doe")
    
    # Mock database execution response
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.check_user_exist(user_id)
    
    # Verify DB execute was called with query
    mock_db_session.execute.assert_called_once()
    assert result == mock_user
    assert result.user_id == user_id


@pytest.mark.asyncio
async def test_check_user_exist_returns_none(repo, mock_db_session):
    """
    Test that check_user_exist returns None if the user does not exist in the database.
    """
    user_id = uuid.uuid4()
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.check_user_exist(user_id)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_credential_by_identifier_success(repo, mock_db_session):
    """
    Test that get_credential_by_identifier searches for credential with correct provider and identifier.
    """
    mock_cred = AuthCredentialModel(
        user_id=uuid.uuid4(),
        provider="email",
        identifier="john@example.com"
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_cred
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_credential_by_identifier(provider="email", identifier="john@example.com")
    
    mock_db_session.execute.assert_called_once()
    assert result == mock_cred


@pytest.mark.asyncio
async def test_get_user_by_credential_success(repo, mock_db_session):
    """
    Test that get_user_by_credential retrieves both user and credential joined in query.
    """
    user_id = uuid.uuid4()
    mock_user = UserModel(user_id=user_id, first_name="John", last_name="Doe")
    mock_cred = AuthCredentialModel(user_id=user_id, provider="username", identifier="john_doe")
    
    mock_result = MagicMock()
    # Mocking result.first() to return a row tuple
    mock_result.first.return_value = (mock_user, mock_cred)
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_user_by_credential(provider="username", identifier="john_doe")
    
    assert result is not None
    user, cred = result
    assert user == mock_user
    assert cred == mock_cred


@pytest.mark.asyncio
async def test_get_user_by_credential_not_found(repo, mock_db_session):
    """
    Test that get_user_by_credential returns None if query returns no rows.
    """
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_user_by_credential(provider="username", identifier="john_doe")
    
    assert result is None


@pytest.mark.asyncio
async def test_create_user_with_credentials(repo, mock_db_session):
    """
    Test that create_user_with_credentials inserts both the UserModel and AuthCredentialModel,
    triggers flush for identity population, and returns the user.
    """
    first_name = "Jane"
    last_name = "Doe"
    provider = "username"
    identifier = "janedoe"
    password_hash = "mock_hashed_pw"
    
    user = await repo.create_user_with_credentials(
        first_name=first_name,
        last_name=last_name,
        provider=provider,
        identifier=identifier,
        password_hash=password_hash
    )
    
    # Assert UserModel and AuthCredentialModel were added to session
    assert mock_db_session.add.call_count == 2
    # Verify flush was called to fetch primary keys/IDs (2 flushes inside create_user_with_credentials)
    assert mock_db_session.flush.call_count == 2
    
    assert isinstance(user, UserModel)
    assert user.first_name == first_name
    assert user.last_name == last_name


@pytest.mark.asyncio
async def test_add_refresh_token(repo, mock_db_session):
    """
    Test that add_refresh_token correctly adds and flushes a RefreshTokenModel record.
    """
    user_id = uuid.uuid4()
    token_hash = "mock_sha256_hash"
    expires_at = datetime.now(timezone.utc)
    
    token = await repo.add_refresh_token(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    
    mock_db_session.add.assert_called_once_with(token)
    mock_db_session.flush.assert_called_once()
    
    assert isinstance(token, RefreshTokenModel)
    assert token.user_id == user_id
    assert token.token_hash == token_hash
    assert token.expires_at == expires_at
