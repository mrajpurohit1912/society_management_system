from typing import Dict, Optional, Type
import structlog

from app.core.config import settings
from app.core.providers.cache.base import AbstractCacheProvider
from app.core.providers.cache.adapters.redis import RedisCacheProvider
from app.core.providers.cache.adapters.memory import InMemoryCacheProvider

logger = structlog.get_logger(__name__)

class CacheProviderFactory:
    """
    Factory & Registry for Cache Strategy Adapters.
    """
    _providers: Dict[str, Type[AbstractCacheProvider]] = {
        "redis": RedisCacheProvider,
        "memory": InMemoryCacheProvider,
    }
    _instance: Optional[AbstractCacheProvider] = None

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> AbstractCacheProvider:
        if cls._instance:
            return cls._instance

        target = (provider_name or getattr(settings, "CACHE_PROVIDER", "memory")).lower()
        provider_cls = cls._providers.get(target, InMemoryCacheProvider)

        if target == "redis":
            try:
                cls._instance = provider_cls(settings.REDIS_URL)
            except Exception as e:
                logger.warning("cache_factory.redis_fallback", error=str(e), fallback="memory")
                cls._instance = InMemoryCacheProvider()
        else:
            cls._instance = InMemoryCacheProvider()

        return cls._instance
