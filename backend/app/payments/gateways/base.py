from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BasePaymentGateway(ABC):
    """
    Abstract Port / Interface for Payment Gateways (Hexagonal Architecture).
    Decouples billing & accounting domain logic from third-party vendor SDKs.
    """

    @abstractmethod
    async def create_order(
        self,
        amount: float,
        currency: str = "INR",
        receipt: str = "",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Initiate payment session or order with gateway provider."""
        pass

    @abstractmethod
    async def verify_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verify cryptographic signature returned by gateway upon checkout."""
        pass

    @abstractmethod
    async def process_refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Issue full or partial refund for a processed payment."""
        pass
