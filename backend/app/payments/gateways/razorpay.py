import os
import uuid
import hmac
import hashlib
from typing import Optional, Dict, Any
import structlog

from app.payments.gateways.base import BasePaymentGateway
from app.payments.gateways.mock import MockPaymentGateway

logger = structlog.get_logger(__name__)


class RazorpayGateway(BasePaymentGateway):
    """
    Razorpay Payment Gateway Adapter.
    If RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET environment variables are set and the
    'razorpay' package is available, processes live sandbox requests.
    Otherwise, gracefully falls back to MockPaymentGateway simulation.
    """

    def __init__(self):
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        self._mock_fallback = MockPaymentGateway()
        self.is_configured = bool(self.key_id and self.key_secret)

        if not self.is_configured:
            logger.info("gateway.razorpay.using_mock_fallback_mode", reason="RAZORPAY_KEY_ID not configured")

    async def create_order(
        self,
        amount: float,
        currency: str = "INR",
        receipt: str = "",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return await self._mock_fallback.create_order(amount, currency, receipt, notes)

        try:
            import razorpay
            client = razorpay.Client(auth=(self.key_id, self.key_secret))
            data = {
                "amount": int(amount * 100),  # Razorpay expects amount in paise
                "currency": currency,
                "receipt": receipt,
                "notes": notes or {},
            }
            order = client.order.create(data=data)
            logger.info("gateway.razorpay.order_created", order_id=order.get("id"), amount=amount)
            return {
                "order_id": order.get("id"),
                "amount": amount,
                "currency": currency,
                "receipt": receipt,
                "status": "created",
                "provider": "razorpay",
            }
        except Exception as e:
            logger.warning("gateway.razorpay.order_create_error_falling_back_to_mock", error=str(e))
            return await self._mock_fallback.create_order(amount, currency, receipt, notes)

    async def verify_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        if not self.is_configured:
            return await self._mock_fallback.verify_signature(order_id, payment_id, signature)

        try:
            msg = f"{order_id}|{payment_id}".encode("utf-8")
            generated_signature = hmac.new(
                self.key_secret.encode("utf-8"),
                msg,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(generated_signature, signature)
        except Exception as e:
            logger.error("gateway.razorpay.signature_verification_failed", error=str(e))
            return False

    async def process_refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return await self._mock_fallback.process_refund(payment_id, amount)

        try:
            import razorpay
            client = razorpay.Client(auth=(self.key_id, self.key_secret))
            data = {"amount": int(amount * 100)} if amount else {}
            refund = client.payment.refund(payment_id, data)
            return {
                "refund_id": refund.get("id"),
                "payment_id": payment_id,
                "amount": amount,
                "status": "processed",
            }
        except Exception as e:
            logger.error("gateway.razorpay.refund_failed", error=str(e))
            raise ValueError(f"Razorpay refund failed: {str(e)}")
