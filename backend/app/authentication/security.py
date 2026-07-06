from datetime import datetime, timedelta, timezone
import hashlib
import os
from typing import Dict, Tuple
import jwt

from app.core.config import settings

# Load security parameters from environment variables (fallback to safe dev values)
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


class TokenService:
    """
    Service responsible for generating, signing, and hashing session tokens (JWT).
    """

    @staticmethod
    def create_access_token(user_id: str) -> str:
        """
        Generate a short-lived JSON Web Token for user API authorization.
        
        Args:
            user_id (str): The unique ID of the authenticated user.
            
        Returns:
            str: Signed JWT access token string.
        """
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: str) -> Tuple[str, str, datetime]:
        """
        Generate a long-lived JWT refresh token and compute its SHA-256 hash.
        
        Returns a tuple of:
            1. The raw signed refresh token (sent back to the client/browser cookie).
            2. The SHA-256 hash of the token (stored securely in the database).
            3. The token expiration timestamp.
            
        Args:
            user_id (str): The unique ID of the user.
            
        Returns:
            Tuple[str, str, datetime]: (raw_token, token_hash, expires_at)
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": user_id,
            "exp": expires_at,
            "type": "refresh"
        }
        raw_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Hash the raw token before database persistence (prevents session theft via database leaks)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        
        return raw_token, token_hash, expires_at

    @staticmethod
    def verify_token(token: str) -> Dict:
        """
        Validate a JWT signature and decode its claims.
        
        Args:
            token (str): Raw JWT token string.
            
        Returns:
            Dict: Decoded token payload claims.
            
        Raises:
            jwt.ExpiredSignatureError: If the token has expired.
            jwt.InvalidTokenError: If the signature is invalid or payload is corrupted.
        """
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
