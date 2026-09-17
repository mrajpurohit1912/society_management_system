import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import structlog
from fastapi import HTTPException, status

from app.payments.services.base import BasePaymentService
from app.payments.models import (
    PaymentModel,
    PaymentReceiptModel,
    InvoiceStatus,
    PaymentStatus,
)
from app.payments.gateways import get_payment_gateway, ManualOfflineGateway
from app.payments.schemas import (
    InitiateOnlinePaymentRequest,
    VerifyOnlinePaymentRequest,
    SubmitOfflinePaymentRequest,
    ReviewOfflinePaymentRequest,
)

logger = structlog.get_logger(__name__)


class TransactionService(BasePaymentService):
    """
    Domain service orchestrating checkout, gateway adapters, offline submissions,
    treasurer approvals, and receipt generation.
    """

    async def initiate_online_payment(
        self, user_id: uuid.UUID, society_id: uuid.UUID, payload: InitiateOnlinePaymentRequest
    ) -> Dict[str, Any]:
        invoice = await self.payment_repo.get_invoice_by_id(payload.invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found.",
            )

        if invoice.status == InvoiceStatus.PAID.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invoice has already been fully paid.",
            )

        amount = payload.amount if payload.amount is not None else invoice.amount

        # Instantiate gateway adapter via factory
        gateway = get_payment_gateway(payload.payment_method)
        receipt_tag = f"INV-{invoice.id.hex[:8].upper()}"
        order_res = await gateway.create_order(
            amount=amount,
            currency="INR",
            receipt=receipt_tag,
            notes={"invoice_id": str(invoice.id), "society_id": str(society_id)},
        )

        payment = PaymentModel(
            society_id=society_id,
            invoice_id=invoice.id,
            unit_id=invoice.unit_id,
            user_id=user_id,
            amount=amount,
            payment_method=payload.payment_method,
            status=PaymentStatus.INITIATED.value,
            gateway_order_id=order_res["order_id"],
        )
        saved = await self.payment_repo.create_payment(payment)

        logger.info(
            "payments.online_payment_initiated",
            payment_id=str(saved.id),
            order_id=order_res["order_id"],
            amount=amount,
        )

        return {
            "payment_id": saved.id,
            "gateway_order_id": order_res["order_id"],
            "amount": amount,
            "currency": "INR",
            "status": saved.status,
            "provider": order_res.get("provider", "mock"),
        }

    async def verify_online_payment(
        self, user_id: uuid.UUID, payload: VerifyOnlinePaymentRequest
    ) -> Dict[str, Any]:
        payment = await self.payment_repo.get_payment_by_id(payload.payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment record not found.",
            )

        if payment.status == PaymentStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment has already been confirmed and processed.",
            )

        gateway = get_payment_gateway(payment.payment_method)
        is_valid = await gateway.verify_signature(
            order_id=payload.gateway_order_id,
            payment_id=payload.gateway_payment_id,
            signature=payload.gateway_signature,
        )

        if not is_valid:
            payment.status = PaymentStatus.FAILED.value
            await self.payment_repo.update_payment(payment)
            logger.warning(
                "payments.online_verification_failed",
                payment_id=str(payment.id),
                order_id=payload.gateway_order_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment verification failed: Invalid cryptographic signature.",
            )

        # Mark payment as COMPLETED
        payment.status = PaymentStatus.COMPLETED.value
        payment.gateway_payment_id = payload.gateway_payment_id
        payment.transaction_reference = payload.gateway_payment_id
        await self.payment_repo.update_payment(payment)

        # Mark invoice as PAID
        invoice = payment.invoice
        if not invoice and payment.invoice_id:
            invoice = await self.payment_repo.get_invoice_by_id(payment.invoice_id)

        if invoice:
            invoice.status = InvoiceStatus.PAID.value
            await self.payment_repo.update_invoice(invoice)

        # Generate official receipt
        receipt = await self._generate_receipt(payment, user_id=user_id)

        logger.info(
            "payments.online_payment_verified_and_completed",
            payment_id=str(payment.id),
            receipt_number=receipt.receipt_number,
        )

        return {
            "success": True,
            "message": "Payment verified and receipt generated successfully.",
            "payment": payment,
            "receipt": receipt,
        }

    async def submit_offline_payment(
        self, user_id: uuid.UUID, society_id: uuid.UUID, payload: SubmitOfflinePaymentRequest
    ) -> PaymentModel:
        invoice = await self.payment_repo.get_invoice_by_id(payload.invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found.",
            )

        if invoice.status == InvoiceStatus.PAID.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invoice has already been settled.",
            )

        if not ManualOfflineGateway.validate_reference(
            payload.payment_method, payload.transaction_reference
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transaction reference (UTR or Cheque Number must be at least 4 characters).",
            )

        payment = PaymentModel(
            society_id=society_id,
            invoice_id=invoice.id,
            unit_id=invoice.unit_id,
            user_id=user_id,
            amount=payload.amount,
            payment_method=payload.payment_method,
            status=PaymentStatus.PENDING_APPROVAL.value,
            transaction_reference=payload.transaction_reference,
            description=payload.description,
        )
        saved = await self.payment_repo.create_payment(payment)

        logger.info(
            "payments.offline_payment_submitted",
            payment_id=str(saved.id),
            ref=payload.transaction_reference,
            method=payload.payment_method,
        )
        return saved

    async def review_offline_payment(
        self, admin_id: uuid.UUID, payment_id: uuid.UUID, payload: ReviewOfflinePaymentRequest
    ) -> PaymentModel:
        payment = await self.payment_repo.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment record not found.",
            )

        if payment.status != PaymentStatus.PENDING_APPROVAL.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment status is '{payment.status}'; only 'pending_approval' payments can be reviewed.",
            )

        if not payload.approved:
            payment.status = PaymentStatus.REJECTED.value
            payment.approved_by = admin_id
            payment.rejection_reason = payload.rejection_reason or "Rejected by Society Admin"
            updated = await self.payment_repo.update_payment(payment)
            logger.info("payments.offline_payment_rejected", payment_id=str(payment_id), admin_id=str(admin_id))
            return updated

        # Approve Payment
        payment.status = PaymentStatus.COMPLETED.value
        payment.approved_by = admin_id
        updated = await self.payment_repo.update_payment(payment)

        # Mark associated invoice as PAID
        invoice = payment.invoice
        if not invoice and payment.invoice_id:
            invoice = await self.payment_repo.get_invoice_by_id(payment.invoice_id)

        if invoice:
            invoice.status = InvoiceStatus.PAID.value
            await self.payment_repo.update_invoice(invoice)

        # Issue formal receipt
        await self._generate_receipt(payment, user_id=payment.user_id)

        logger.info(
            "payments.offline_payment_approved",
            payment_id=str(payment_id),
            admin_id=str(admin_id),
        )
        return updated

    async def get_payment_receipt(self, payment_id: uuid.UUID) -> PaymentReceiptModel:
        receipt = await self.payment_repo.get_receipt_by_payment_id(payment_id)
        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found for this payment.",
            )
        return receipt

    async def list_pending_offline_payments(self, society_id: uuid.UUID) -> List[PaymentModel]:
        return await self.payment_repo.list_pending_approvals(society_id)

    async def get_society_collection_summary(self, society_id: uuid.UUID) -> Dict[str, Any]:
        return await self.payment_repo.get_collection_summary(society_id)

    # ---------------------------------------------------------
    # Helper: Receipt Generator
    # ---------------------------------------------------------

    async def _generate_receipt(
        self, payment: PaymentModel, user_id: uuid.UUID
    ) -> PaymentReceiptModel:
        # Prevent duplicate receipts
        existing = await self.payment_repo.get_receipt_by_payment_id(payment.id)
        if existing:
            return existing

        user = await self.user_repo.get_user_by_id(user_id)
        unit = await self.society_repo.get_unit(payment.unit_id) if payment.unit_id else None
        society = await self.society_repo.get_society(payment.society_id)

        issued_to = f"{user.first_name} {user.last_name}" if user else "Resident"
        unit_str = f"Unit {unit.unit_number}" if unit else "N/A"
        society_name = society.name if society else "Society"

        receipt_number = f"REC-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

        receipt = PaymentReceiptModel(
            payment_id=payment.id,
            receipt_number=receipt_number,
            invoice_id=payment.invoice_id,
            amount_paid=payment.amount,
            issued_to_name=issued_to,
            unit_number=unit_str,
            society_name=society_name,
        )
        return await self.payment_repo.create_receipt(receipt)
