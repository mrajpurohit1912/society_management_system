

import redis.asyncio as redis                                                                                                                                       

from app.core.config import settings

class RedisService:                                                                                                                                                 
    """                                                                                                                                                             
    Service class responsible for interfacing with Redis.                                                                                                           
    Uses redis-py async client to handle key-value caching.                                                                                                         
    """                                                                                                                                                             
    def __init__(self):                                                                                                                                             
        self.redis_url = settings.REDIS_URL                                                                                        
        self.client = redis.from_url(self.redis_url, decode_responses=True)                                                                                         

    async def verify_otp(self, phone: str, otp_code: str) -> bool:
        """
        Retrieves the OTP stored for the given phone number and verifies it.
        """
        # Look up the stored OTP code (assuming keys are stored as "otp:{phone_number}")
        stored_otp = await self.client.get(f"otp:{phone}")
        if not stored_otp:
            return False
            
        return stored_otp == otp_code

    async def invalidate_otp(self, phone: str) -> None:
        """Deletes the stored OTP from Redis so it cannot be reused."""
        await self.client.delete(f"otp:{phone}")