import uuid
from typing import Optional, Dict, Any
import structlog

from app.payments.gateways.base import BasePaymentGateway

logger = structlog.get_logger(__name__)


class ManualOfflineGateway(BasePaymentGateway):
    """
    Manual Offline Payment Gateway Adapter.
    Handles Direct Bank Transfers (NEFT/IMPS/UPI UTR), Cheques, and Cash receipts.
    Transactions are queued with 'pending_approval' status for Society Treasurer / Admin verification.
    """

    async def create_order(
        self,
        amount: float,
        currency: str = "INR",
        receipt: str = "",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ref_id = f"OFFLINE-{uuid.uuid4().hex[:8].upper()}"
        logger.info(
            "gateway.manual.order_initiated",
            ref_id=ref_id,
            amount=amount,
            notes=notes,
        )
        return {
            "order_id": ref_id,
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "status": "awaiting_offline_submission",
            "provider": "manual_offline",
        }

    async def verify_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """
        Offline payments don't rely on cryptographic webhooks.
        Verification is performed by society administrators/treasurers during audit.
        """
        return True

    async def process_refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        return {
            "refund_id": f"REFUND-OFFLINE-{uuid.uuid4().hex[:8].upper()}",
            "payment_id": payment_id,
            "amount": amount,
            "status": "manual_refund_logged",
        }

    @staticmethod
    def validate_reference(payment_method: str, reference: Optional[str]) -> bool:
        """Validates that a valid reference (UTR or Cheque No) is provided."""
        if not reference or len(reference.strip()) < 4:
            return False
        return True
