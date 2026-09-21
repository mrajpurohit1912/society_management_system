import uuid
from typing import Optional, List
import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.authentication.dependencies import require_security_or_admin
from app.authentication.models import UserModel
from app.visitors.schemas import (
    PasscodeCheckInRequest,
    QRCheckInRequest,
    QuickCheckInRequest,
    CheckOutRequest,
    VisitorLogResponse,
    ActiveVisitorsSummary,
)
from app.visitors.services.gatekeeper_service import GatekeeperService
from app.visitors.routes.common import safe_transaction

router = APIRouter(tags=["Gatekeeper Operations"])
logger = structlog.get_logger(__name__)


@router.post(
    "/societies/{society_id}/gatekeeper/verify-passcode",
    response_model=VisitorLogResponse,
    status_code=status.HTTP_200_OK,
)
async def checkin_with_passcode(
    society_id: uuid.UUID,
    payload: PasscodeCheckInRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_security_or_admin),
):
    """
    Gatekeeper Endpoint: Validate resident-generated 6-digit passcode and check in visitor.
    """
    service = GatekeeperService(db)
    async with safe_transaction(db):
        log_record = await service.verify_and_checkin_passcode(
            guard_id=current_user.user_id,
            society_id=society_id,
            payload=payload,
        )
    return log_record


@router.post(
    "/societies/{society_id}/gatekeeper/verify-qr",
    response_model=VisitorLogResponse,
    status_code=status.HTTP_200_OK,
)
async def checkin_with_qr(
    society_id: uuid.UUID,
    payload: QRCheckInRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_security_or_admin),
):
    """
    Gatekeeper Endpoint: Validate resident-generated QR code token and check in visitor.
    """
    service = GatekeeperService(db)
    async with safe_transaction(db):
        log_record = await service.verify_and_checkin_qr(
            guard_id=current_user.user_id,
            society_id=society_id,
            payload=payload,
        )
    return log_record


@router.post(
    "/societies/{society_id}/gatekeeper/quick-checkin",
    response_model=VisitorLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def quick_checkin(
    society_id: uuid.UUID,
    payload: QuickCheckInRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_security_or_admin),
):
    """
    Gatekeeper Endpoint: Quick check-in for delivery agents, cab drivers, or walk-ins.
    """
    service = GatekeeperService(db)
    async with safe_transaction(db):
        log_record = await service.quick_checkin(
            guard_id=current_user.user_id,
            society_id=society_id,
            payload=payload,
        )
    return log_record


@router.post(
    "/societies/{society_id}/gatekeeper/logs/{log_id}/checkout",
    response_model=VisitorLogResponse,
    status_code=status.HTTP_200_OK,
)
async def checkout_visitor(
    society_id: uuid.UUID,
    log_id: uuid.UUID,
    payload: CheckOutRequest = CheckOutRequest(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_security_or_admin),
):
    """
    Gatekeeper Endpoint: Log visitor checkout from society premises.
    """
    service = GatekeeperService(db)
    async with safe_transaction(db):
        log_record = await service.checkout_visitor(
            guard_id=current_user.user_id,
            society_id=society_id,
            log_id=log_id,
            payload=payload,
        )
    return log_record


@router.get(
    "/societies/{society_id}/gatekeeper/active",
    response_model=List[VisitorLogResponse],
)
async def list_active_visitors(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_security_or_admin),
):
    """
    Gatekeeper Endpoint: Get all visitors currently inside society premises.
    """
    service = GatekeeperService(db)
    return await service.list_active_visitors(society_id=society_id)


@router.get(
    "/societies/{society_id}/gatekeeper/logs",
    response_model=List[VisitorLogResponse],
)
async def list_visitor_logs(
    society_id: uuid.UUID,
    status: Optional[str] = None,
    visitor_type: Optional[str] = None,
    unit_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_security_or_admin),
):
    """
    Gatekeeper Endpoint: Query visitor log history with optional filters.
    """
    service = GatekeeperService(db)
    return await service.list_visitor_logs(
        society_id=society_id,
        status_filter=status,
        visitor_type=visitor_type,
        unit_id=unit_id,
    )


@router.get(
    "/societies/{society_id}/gatekeeper/summary",
    response_model=ActiveVisitorsSummary,
)
async def get_visitors_summary(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_security_or_admin),
):
    """
    Gatekeeper Dashboard Endpoint: Live metrics on visitors inside and overstay alerts (>4h).
    """
    service = GatekeeperService(db)
    summary_data = await service.get_active_summary(society_id=society_id)
    return summary_data
