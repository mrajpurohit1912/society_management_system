import uuid
from typing import Optional, List, Dict, Any
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_society_admin
from app.authentication.models import UserModel
from app.payments.schemas import (
    InitiateOnlinePaymentRequest,
    InitiateOnlinePaymentResponse,
    VerifyOnlinePaymentRequest,
    SubmitOfflinePaymentRequest,
    ReviewOfflinePaymentRequest,
    PaymentResponse,
    ReceiptResponse,
    SocietyCollectionSummary,
)
from app.payments.services.transaction_service import TransactionService
from app.payments.routes.common import safe_transaction

router = APIRouter(tags=["Payment Transactions & Receipts"])
logger = structlog.get_logger(__name__)


@router.post(
    "/societies/{society_id}/payments/initiate",
    response_model=InitiateOnlinePaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_online_payment(
    society_id: uuid.UUID,
    payload: InitiateOnlinePaymentRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Resident Endpoint: Initiate an online checkout order (Mock or Razorpay Sandbox).
    Returns order details and gateway credentials needed by frontend checkout widgets.
    """
    service = TransactionService(db)
    async with safe_transaction(db):
        res = await service.initiate_online_payment(
            user_id=current_user.user_id,
            society_id=society_id,
            payload=payload,
        )
    return res


@router.post(
    "/payments/verify",
    status_code=status.HTTP_200_OK,
)
async def verify_online_payment(
    payload: VerifyOnlinePaymentRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Resident Endpoint: Verify online payment cryptographic signature,
    confirm invoice settlement, and automatically issue a formal receipt.
    """
    service = TransactionService(db)
    async with safe_transaction(db):
        res = await service.verify_online_payment(
            user_id=current_user.user_id,
            payload=payload,
        )
    return {
        "success": True,
        "message": res["message"],
        "payment_id": str(res["payment"].id),
        "receipt_number": res["receipt"].receipt_number,
        "status": res["payment"].status,
    }


@router.post(
    "/societies/{society_id}/payments/submit-offline",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_offline_payment(
    society_id: uuid.UUID,
    payload: SubmitOfflinePaymentRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Resident Endpoint: Submit offline payment proof (Direct Bank Transfer UTR,
    Cheque Number, or Cash deposit). Queued for Society Admin verification.
    """
    service = TransactionService(db)
    async with safe_transaction(db):
        payment = await service.submit_offline_payment(
            user_id=current_user.user_id,
            society_id=society_id,
            payload=payload,
        )
    return payment


@router.get(
    "/societies/{society_id}/payments/pending-approval",
    response_model=List[PaymentResponse],
)
async def list_pending_offline_payments(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Society Admin Endpoint: View audit queue of offline payments awaiting verification.
    """
    service = TransactionService(db)
    return await service.list_pending_offline_payments(society_id)


@router.post(
    "/societies/{society_id}/payments/{payment_id}/review",
    response_model=PaymentResponse,
)
async def review_offline_payment(
    society_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: ReviewOfflinePaymentRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Society Admin Endpoint: Approve or reject an offline maintenance payment.
    If approved, marks invoice as PAID and generates an official receipt.
    """
    service = TransactionService(db)
    async with safe_transaction(db):
        payment = await service.review_offline_payment(
            admin_id=current_user.user_id,
            payment_id=payment_id,
            payload=payload,
        )
    return payment


@router.get(
    "/payments/{payment_id}/receipt",
    response_model=ReceiptResponse,
)
async def get_payment_receipt(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get official payment receipt for an approved or completed payment.
    """
    service = TransactionService(db)
    return await service.get_payment_receipt(payment_id)


@router.get(
    "/societies/{society_id}/collection-summary",
    response_model=SocietyCollectionSummary,
)
async def get_society_collection_summary(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Society Admin Endpoint: View high-level billing & collection metrics.
    """
    service = TransactionService(db)
    return await service.get_society_collection_summary(society_id)
