import uuid
import hashlib
from typing import Optional, Dict, Any
import structlog

from app.payments.gateways.base import BasePaymentGateway

logger = structlog.get_logger(__name__)


class MockPaymentGateway(BasePaymentGateway):
    """
    Mock Payment Gateway Adapter.
    Provides 100% deterministic, zero-cost, offline payment simulation for development,
    testing, and CI/CD pipelines without requiring any external accounts.
    """

    async def create_order(
        self,
        amount: float,
        currency: str = "INR",
        receipt: str = "",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        order_id = f"order_mock_{uuid.uuid4().hex[:12]}"
        logger.info(
            "gateway.mock.order_created",
            order_id=order_id,
            amount=amount,
            currency=currency,
            receipt=receipt,
        )
        return {
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "provider": "mock",
        }

    async def verify_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        # Simulate payment failure if client passes payment_id starting with 'fail_'
        if payment_id.startswith("fail_"):
            logger.warning(
                "gateway.mock.signature_verification_simulated_failure",
                order_id=order_id,
                payment_id=payment_id,
            )
            return False

        logger.info(
            "gateway.mock.signature_verified_success",
            order_id=order_id,
            payment_id=payment_id,
        )
        return True

    async def process_refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        refund_id = f"rfnd_mock_{uuid.uuid4().hex[:12]}"
        logger.info(
            "gateway.mock.refund_processed",
            refund_id=refund_id,
            payment_id=payment_id,
            amount=amount,
        )
        return {
            "refund_id": refund_id,
            "payment_id": payment_id,
            "amount": amount,
            "status": "processed",
        }
