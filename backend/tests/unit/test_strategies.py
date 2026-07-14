import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import bcrypt

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
    hash_password,
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
    AdminSignupRequest,
)


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def user_mock():
    user = MagicMock()
    user.user_id = "user-uuid-123"
    user.first_name = "John"
    user.last_name = "Doe"
    return user


@pytest.fixture
def credential_mock():
    cred = MagicMock()
    cred.user_id = "user-uuid-123"
    cred.provider = "username"
    cred.identifier = "testuser"
    cred.password_hash = hash_password("password123")
    return cred


# ==============================================================================
# 1. UsernamePasswordStrategy Tests
# ==============================================================================

@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_username_password_signup_success(mock_user_repo_cls, mock_db, user_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    
    mock_repo_inst.get_credential_by_identifier.return_value = None
    mock_repo_inst.create_user_with_credentials.return_value = user_mock
    
    strategy = UsernamePasswordStrategy()
    payload = UsernamePasswordSignupRequest(
        first_name="John", last_name="Doe", username="testuser", password="password123"
    )
    
    result = await strategy.signup(mock_db, payload)
    
    mock_repo_inst.get_credential_by_identifier.assert_called_once_with(
        provider="username", identifier="testuser"
    )
    mock_repo_inst.create_user_with_credentials.assert_called_once()
    assert result == user_mock


@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_username_password_signup_username_taken(mock_user_repo_cls, mock_db, credential_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    mock_repo_inst.get_credential_by_identifier.return_value = credential_mock
    
    strategy = UsernamePasswordStrategy()
    payload = UsernamePasswordSignupRequest(
        first_name="John", last_name="Doe", username="testuser", password="password123"
    )
    
    with pytest.raises(ValueError) as exc_info:
        await strategy.signup(mock_db, payload)
        
    assert "Username is already taken" in str(exc_info.value)
    mock_repo_inst.create_user_with_credentials.assert_not_called()


# ==============================================================================
# 2. EmailPasswordStrategy Tests
# ==============================================================================

@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_email_password_signup_success(mock_user_repo_cls, mock_db, user_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    mock_repo_inst.get_credential_by_identifier.return_value = None
    mock_repo_inst.create_user_with_credentials.return_value = user_mock
    
    strategy = EmailPasswordStrategy()
    payload = EmailPasswordSignupRequest(
        first_name="John", last_name="Doe", email="johndoe@example.com", password="password123"
    )
    
    result = await strategy.signup(mock_db, payload)
    
    mock_repo_inst.get_credential_by_identifier.assert_called_once_with(
        provider="email", identifier="johndoe@example.com"
    )
    assert result == user_mock


@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_email_password_signup_email_taken(mock_user_repo_cls, mock_db, credential_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    mock_repo_inst.get_credential_by_identifier.return_value = credential_mock
    
    strategy = EmailPasswordStrategy()
    payload = EmailPasswordSignupRequest(
        first_name="John", last_name="Doe", email="johndoe@example.com", password="password123"
    )
    
    with pytest.raises(ValueError) as exc_info:
        await strategy.signup(mock_db, payload)
        
    assert "Email is already registered" in str(exc_info.value)


# ==============================================================================
# 3. MobileOTPStrategy Tests
# ==============================================================================

@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_mobile_otp_signup_success(mock_user_repo_cls, mock_db, mock_redis, user_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    
    # 1. Valid OTP check
    mock_redis.verify_otp.return_value = True
    # 2. Number is not registered
    mock_repo_inst.get_credential_by_identifier.return_value = None
    mock_repo_inst.create_user_with_credentials.return_value = user_mock
    
    strategy = MobileOTPStrategy(mock_redis)
    payload = MobileOTPSignupRequest(
        first_name="John", last_name="Doe", phone_number="+1234567890", otp_code="123456"
    )
    
    result = await strategy.signup(mock_db, payload)
    
    mock_redis.verify_otp.assert_called_once_with(phone="+1234567890", otp_code="123456")
    mock_repo_inst.get_credential_by_identifier.assert_called_once_with(
        provider="phone", identifier="+1234567890"
    )
    mock_redis.invalidate_otp.assert_called_once_with("+1234567890")
    assert result == user_mock


@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_mobile_otp_signup_invalid_otp(mock_user_repo_cls, mock_db, mock_redis):
    # Mock invalid OTP
    mock_redis.verify_otp.return_value = False
    
    strategy = MobileOTPStrategy(mock_redis)
    payload = MobileOTPSignupRequest(
        first_name="John", last_name="Doe", phone_number="+1234567890", otp_code="123456"
    )
    
    with pytest.raises(ValueError) as exc_info:
        await strategy.signup(mock_db, payload)
        
    assert "Invalid or expired OTP code" in str(exc_info.value)
    mock_redis.verify_otp.assert_called_once()
    mock_redis.invalidate_otp.assert_not_called()


# ==============================================================================
# 4. GoogleStrategy Tests
# ==============================================================================

@pytest.mark.asyncio
@patch("app.authentication.strategies.id_token.verify_oauth2_token")
@patch("app.authentication.strategies.UserRepository")
async def test_google_signup_new_user(mock_user_repo_cls, mock_verify_oauth, mock_db, user_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    
    # 1. Google token validation returns payload
    mock_verify_oauth.return_value = {
        "sub": "google-sub-id",
        "email": "googleuser@example.com",
        "given_name": "GoogleFirst",
        "family_name": "GoogleLast",
    }
    
    # 2. User is not yet registered in DB
    mock_repo_inst.get_credential_by_identifier.return_value = None
    mock_repo_inst.create_user_with_credentials.return_value = user_mock
    
    strategy = GoogleStrategy(google_client_id="dummy-google-client-id")
    payload = GoogleSignupRequest(google_id_token="google-raw-jwt-token")
    
    result = await strategy.signup(mock_db, payload)
    
    mock_verify_oauth.assert_called_once()
    mock_repo_inst.get_credential_by_identifier.assert_called_once_with(
        provider="google", identifier="google-sub-id"
    )
    mock_repo_inst.create_user_with_credentials.assert_called_once_with(
        first_name="GoogleFirst",
        last_name="GoogleLast",
        provider="google",
        identifier="google-sub-id",
        password_hash=None
    )
    assert result == user_mock


@pytest.mark.asyncio
@patch("app.authentication.strategies.id_token.verify_oauth2_token")
@patch("app.authentication.strategies.UserRepository")
async def test_google_signup_existing_user(mock_user_repo_cls, mock_verify_oauth, mock_db, user_mock, credential_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    
    mock_verify_oauth.return_value = {"sub": "google-sub-id"}
    
    # User is registered, return credential linked to user
    mock_repo_inst.get_credential_by_identifier.return_value = credential_mock
    mock_repo_inst.get_user_by_id.return_value = user_mock
    
    strategy = GoogleStrategy(google_client_id="dummy-google-client-id")
    payload = GoogleSignupRequest(google_id_token="google-raw-jwt-token")
    
    result = await strategy.signup(mock_db, payload)
    
    mock_repo_inst.get_user_by_id.assert_called_once_with(credential_mock.user_id)
    mock_repo_inst.create_user_with_credentials.assert_not_called()
    assert result == user_mock


@pytest.mark.asyncio
@patch("app.authentication.strategies.id_token.verify_oauth2_token")
async def test_google_signup_invalid_token(mock_verify_oauth, mock_db):
    # Verification raises an error (expired or invalid signature)
    mock_verify_oauth.side_effect = Exception("Signature verification failed")
    
    strategy = GoogleStrategy(google_client_id="dummy-google-client-id")
    payload = GoogleSignupRequest(google_id_token="invalid-token")
    
    with pytest.raises(ValueError) as exc_info:
        await strategy.signup(mock_db, payload)
        
    assert "Invalid Google OAuth token" in str(exc_info.value)


# ==============================================================================
# 4.5. AdminSignupStrategy Tests
# ==============================================================================

@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_admin_signup_success(mock_user_repo_cls, mock_db, user_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    
    mock_repo_inst.get_credential_by_identifier.return_value = None
    mock_repo_inst.create_user_with_credentials.return_value = user_mock
    
    strategy = AdminSignupStrategy(admin_secret="super-secret-key")
    payload = AdminSignupRequest(
        first_name="AdminFirst",
        last_name="AdminLast",
        email="admin@example.com",
        password="password123",
        admin_secret="super-secret-key"
    )
    
    result = await strategy.signup(mock_db, payload)
    
    mock_repo_inst.get_credential_by_identifier.assert_called_once_with(
        provider="email", identifier="admin@example.com"
    )
    mock_repo_inst.create_user_with_credentials.assert_called_once()
    # Check that it passed role="admin"
    args, kwargs = mock_repo_inst.create_user_with_credentials.call_args
    assert kwargs.get("role") == "admin"
    assert result == user_mock


@pytest.mark.asyncio
async def test_admin_signup_invalid_secret(mock_db):
    strategy = AdminSignupStrategy(admin_secret="super-secret-key")
    payload = AdminSignupRequest(
        first_name="AdminFirst",
        last_name="AdminLast",
        email="admin@example.com",
        password="password123",
        admin_secret="wrong-secret-key"
    )
    
    with pytest.raises(ValueError) as exc_info:
        await strategy.signup(mock_db, payload)
        
    assert "Invalid administrator registration secret" in str(exc_info.value)


@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_admin_signup_email_taken(mock_user_repo_cls, mock_db, credential_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    mock_repo_inst.get_credential_by_identifier.return_value = credential_mock
    
    strategy = AdminSignupStrategy(admin_secret="super-secret-key")
    payload = AdminSignupRequest(
        first_name="AdminFirst",
        last_name="AdminLast",
        email="admin@example.com",
        password="password123",
        admin_secret="super-secret-key"
    )
    
    with pytest.raises(ValueError) as exc_info:
        await strategy.signup(mock_db, payload)
        
    assert "Email is already registered" in str(exc_info.value)


# ==============================================================================
# 5. UsernameSigninStrategy Tests
# ==============================================================================

@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_username_signin_success(mock_user_repo_cls, mock_db, user_mock, credential_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    
    mock_repo_inst.get_user_by_credential.return_value = (user_mock, credential_mock)
    
    strategy = UsernameSigninStrategy()
    payload = UsernameSigninRequest(username="testuser", password="password123")
    
    result = await strategy.signin(mock_db, payload)
    
    mock_repo_inst.get_user_by_credential.assert_called_once_with(
        provider="username", identifier="testuser"
    )
    assert result == user_mock


@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_username_signin_invalid_password(mock_user_repo_cls, mock_db, user_mock, credential_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    mock_repo_inst.get_user_by_credential.return_value = (user_mock, credential_mock)
    
    strategy = UsernameSigninStrategy()
    # Signin request with an incorrect password
    payload = UsernameSigninRequest(username="testuser", password="wrongpassword")
    
    with pytest.raises(ValueError) as exc_info:
        await strategy.signin(mock_db, payload)
        
    assert "Invalid username or password" in str(exc_info.value)


# ==============================================================================
# 6. MobileOTPSigninStrategy Tests
# ==============================================================================

@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_mobile_otp_signin_success(mock_user_repo_cls, mock_db, mock_redis, user_mock, credential_mock):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    
    mock_redis.verify_otp.return_value = True
    mock_repo_inst.get_user_by_credential.return_value = (user_mock, credential_mock)
    
    strategy = MobileOTPSigninStrategy(mock_redis)
    payload = MobileOTPSigninRequest(phone_number="+1234567890", otp_code="123456")
    
    result = await strategy.signin(mock_db, payload)
    
    mock_redis.verify_otp.assert_called_once_with(phone="+1234567890", otp_code="123456")
    mock_repo_inst.get_user_by_credential.assert_called_once_with(
        provider="phone", identifier="+1234567890"
    )
    mock_redis.invalidate_otp.assert_called_once_with("+1234567890")
    assert result == user_mock


@pytest.mark.asyncio
@patch("app.authentication.strategies.UserRepository")
async def test_mobile_otp_signin_not_registered(mock_user_repo_cls, mock_db, mock_redis):
    mock_repo_inst = AsyncMock()
    mock_user_repo_cls.return_value = mock_repo_inst
    
    mock_redis.verify_otp.return_value = True
    # User is not registered in the database
    mock_repo_inst.get_user_by_credential.return_value = None
    
    strategy = MobileOTPSigninStrategy(mock_redis)
    payload = MobileOTPSigninRequest(phone_number="+1234567890", otp_code="123456")
    
    with pytest.raises(ValueError) as exc_info:
        await strategy.signin(mock_db, payload)
        
    assert "Phone number is not registered" in str(exc_info.value)
    mock_redis.invalidate_otp.assert_not_called()
