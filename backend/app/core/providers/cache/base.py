from abc import ABC, abstractmethod

class AbstractCacheProvider(ABC):
    """
    Abstract Port Interface for Cache Providers.
    Fulfills Dependency Inversion Principle (DIP).
    """

    @abstractmethod
    async def set_otp(self, phone: str, otp_code: str, ttl_seconds: int = 300) -> None:
        """Stores an OTP for a given phone number with TTL."""
        pass

    @abstractmethod
    async def verify_otp(self, phone: str, otp_code: str) -> bool:
        """Retrieves and verifies the OTP for a phone number."""
        pass

    @abstractmethod
    async def invalidate_otp(self, phone: str) -> None:
        """Deletes stored OTP."""
        pass
