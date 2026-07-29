import time
from typing import Dict, Tuple
from app.core.providers.cache.base import AbstractCacheProvider

class InMemoryCacheProvider(AbstractCacheProvider):
    """
    Concrete Strategy Adapter for In-Memory Dictionary Cache with TTL.
    """
    def __init__(self):
        self._store: Dict[str, Tuple[str, float]] = {}

    async def set_otp(self, phone: str, otp_code: str, ttl_seconds: int = 300) -> None:
        expiry = time.time() + ttl_seconds
        self._store[f"otp:{phone}"] = (otp_code, expiry)

    async def verify_otp(self, phone: str, otp_code: str) -> bool:
        key = f"otp:{phone}"
        record = self._store.get(key)
        if not record:
            return False
        stored_code, expiry = record
        if time.time() > expiry:
            del self._store[key]
            return False
        return stored_code == otp_code

    async def invalidate_otp(self, phone: str) -> None:
        key = f"otp:{phone}"
        self._store.pop(key, None)
