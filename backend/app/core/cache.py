from app.core.providers.cache import AbstractCacheProvider, CacheProviderFactory

# Clean Facade forwarding calls to the configured AbstractCacheProvider via CacheProviderFactory
class RedisService:
    def __init__(self):
        self._provider: AbstractCacheProvider = CacheProviderFactory.get_provider()

    async def set_otp(self, phone: str, otp_code: str, ttl_seconds: int = 300) -> None:
        await self._provider.set_otp(phone, otp_code, ttl_seconds)

    async def verify_otp(self, phone: str, otp_code: str) -> bool:
        return await self._provider.verify_otp(phone, otp_code)

    async def invalidate_otp(self, phone: str) -> None:
        await self._provider.invalidate_otp(phone)