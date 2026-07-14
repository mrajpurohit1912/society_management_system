import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
import jwt

from app.authentication.security import (
    TokenService,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


@pytest.fixture
def mock_utc_now():
    """Provides a fixed, timezone-aware datetime for testing to prevent timing flakiness."""
    return datetime(2026, 7, 8, 12, 0, 0, tzinfo=timezone.utc)


def test_create_access_token_success(mock_utc_now):
    """
    Test that an access token is generated with the correct subject, expiration, and payload structure.
    """
    user_id = "user_12345"

    with patch("app.authentication.security.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_utc_now
        # Keep timezone reference working
        mock_datetime.timezone = timezone
        
        token = TokenService.create_access_token(user_id, "member")

    # Decode token using PyJWT directly to inspect raw claims (ignoring exp check for mock timing)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})

    assert payload["sub"] == user_id
    assert payload["role"] == "member"
    assert payload["type"] == "access"
    
    # Expiration assertion: 12:00:00 + 15 minutes = 12:15:00
    expected_exp = int((mock_utc_now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
    assert payload["exp"] == expected_exp


def test_create_refresh_token_success(mock_utc_now):
    """
    Test that a refresh token tuple contains:
    1. A valid raw JWT token
    2. The exact SHA-256 hash of that raw token
    3. The correct expiration datetime
    """
    user_id = "user_12345"

    with patch("app.authentication.security.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_utc_now
        mock_datetime.timezone = timezone
        
        raw_token, token_hash, expires_at = TokenService.create_refresh_token(user_id)

    # Decode refresh token using PyJWT directly to inspect claims (ignoring exp check for mock timing)
    payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})

    # Assert payload claims
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    
    expected_exp_dt = mock_utc_now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    expected_exp_timestamp = int(expected_exp_dt.timestamp())
    assert payload["exp"] == expected_exp_timestamp

    # Assert returned expiration matches the datetime object returned
    assert expires_at == expected_exp_dt

    # Assert returned hash matches the SHA-256 hex digest of the raw token
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    assert token_hash == expected_hash


def test_verify_token_success():
    """
    Test that verification decodes claims successfully for a valid, unexpired token.
    """
    user_id = "user_9999"
    token = TokenService.create_access_token(user_id, "member")

    decoded_payload = TokenService.verify_token(token)

    assert decoded_payload["sub"] == user_id
    assert decoded_payload["type"] == "access"
    assert "exp" in decoded_payload


def test_verify_token_expired(mock_utc_now):
    """
    Test that TokenService raises ExpiredSignatureError when verify_token is called with an expired token.
    """
    user_id = "user_expired"
    past_time = mock_utc_now - timedelta(days=1)
    
    # Generate token set in the past
    with patch("app.authentication.security.datetime") as mock_datetime:
        mock_datetime.now.return_value = past_time
        mock_datetime.timezone = timezone
        token = TokenService.create_access_token(user_id, "member")

    # Verification must raise ExpiredSignatureError
    with pytest.raises(jwt.ExpiredSignatureError):
        TokenService.verify_token(token)


def test_verify_token_invalid_signature():
    """
    Test that TokenService raises InvalidSignatureError when verify_token is called with a token
    signed using a different key.
    """
    user_id = "user_unauthorized"
    wrong_key = "completely_different_secret_key_123456789"
    
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "type": "access"
    }
    invalid_token = jwt.encode(payload, wrong_key, algorithm=ALGORITHM)

    with pytest.raises(jwt.InvalidSignatureError):
        TokenService.verify_token(invalid_token)


def test_verify_token_decode_error():
    """
    Test that TokenService raises DecodeError for completely malformed token strings.
    """
    malformed_token = "not.a.valid.jwt.token"

    with pytest.raises(jwt.DecodeError):
        TokenService.verify_token(malformed_token)