from datetime import datetime, timedelta, timezone
import hashlib
import bcrypt
import os
from typing import Dict, Tuple
import jwt

from app.core.config import settings

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


class PasswordHasher:
    """
    Utility class for hashing and verifying passwords using native bcrypt.
    """
    @staticmethod
    def hash_password(password: str) -> str:
        pwd_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False


class TokenService:
    """
    Service responsible for generating, signing, and hashing session tokens (JWT).
    """

    @staticmethod
    def create_access_token(user_id: str, role: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "role": role,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: str) -> Tuple[str, str, datetime]:
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": user_id,
            "exp": expires_at,
            "type": "refresh"
        }
        raw_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        return raw_token, token_hash, expires_at

    @staticmethod
    def verify_token(token: str) -> Dict:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
