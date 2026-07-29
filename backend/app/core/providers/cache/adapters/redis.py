import redis.asyncio as redis
from app.core.providers.cache.base import AbstractCacheProvider

class RedisCacheProvider(AbstractCacheProvider):
    """
    Concrete Strategy Adapter for Redis Client.
    """
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = redis.from_url(redis_url, decode_responses=True)

    async def set_otp(self, phone: str, otp_code: str, ttl_seconds: int = 300) -> None:
        await self.client.setex(f"otp:{phone}", ttl_seconds, otp_code)

    async def verify_otp(self, phone: str, otp_code: str) -> bool:
        stored_otp = await self.client.get(f"otp:{phone}")
        if not stored_otp:
            return False
        return stored_otp == otp_code

    async def invalidate_otp(self, phone: str) -> None:
        await self.client.delete(f"otp:{phone}")
