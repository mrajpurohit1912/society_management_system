import uuid
from typing import Optional, List
import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.authentication.dependencies import require_society_member, require_society_admin
from app.authentication.models import UserModel
from app.notices.schemas import (
    NoticeCreate,
    NoticeUpdate,
    NoticeResponse,
    NoticeReadReceiptResponse,
    NoticeStatsResponse,
)
from app.notices.services.notice_service import NoticeService
from app.notices.routes.common import safe_transaction

router = APIRouter(tags=["Notice Board & Communications"])
logger = structlog.get_logger(__name__)


@router.post(
    "/societies/{society_id}/notices",
    response_model=NoticeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def publish_notice(
    society_id: uuid.UUID,
    payload: NoticeCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Admin Endpoint: Publish a new notice/circular (can be pinned, categorized, and audience targeted).
    """
    service = NoticeService(db)
    async with safe_transaction(db):
        notice = await service.publish_notice(
            user_id=current_user.user_id,
            society_id=society_id,
            payload=payload,
        )
    return await service.get_notice(society_id, notice.id)


@router.get(
    "/societies/{society_id}/notices",
    response_model=List[NoticeResponse],
)
async def list_active_notices(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_member),
):
    """
    Resident Endpoint: View all active circulars targeted to this resident (pinned notices first).
    """
    service = NoticeService(db)
    return await service.list_active_notices_for_user(
        society_id=society_id, user_id=current_user.user_id
    )


@router.get(
    "/societies/{society_id}/notices/admin",
    response_model=List[NoticeResponse],
)
async def list_all_notices_admin(
    society_id: uuid.UUID,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Admin Endpoint: View all notices (active and archived) for management review.
    """
    service = NoticeService(db)
    return await service.list_all_notices_admin(
        society_id=society_id, category=category, priority=priority
    )


@router.get(
    "/societies/{society_id}/notices/{notice_id}",
    response_model=NoticeResponse,
)
async def get_notice_details(
    society_id: uuid.UUID,
    notice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_member),
):
    """
    View notice details. Automatically logs a read receipt for audit tracking.
    """
    service = NoticeService(db)
    async with safe_transaction(db):
        notice_dict = await service.get_notice(
            society_id=society_id,
            notice_id=notice_id,
            current_user_id=current_user.user_id,
        )
    return notice_dict


@router.patch(
    "/societies/{society_id}/notices/{notice_id}",
    response_model=NoticeResponse,
)
async def update_notice(
    society_id: uuid.UUID,
    notice_id: uuid.UUID,
    payload: NoticeUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Admin Endpoint: Update notice content, pinning status, or expiration.
    """
    service = NoticeService(db)
    async with safe_transaction(db):
        await service.update_notice(
            admin_user_id=current_user.user_id,
            society_id=society_id,
            notice_id=notice_id,
            payload=payload,
        )
    return await service.get_notice(society_id, notice_id)


@router.delete(
    "/societies/{society_id}/notices/{notice_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_notice(
    society_id: uuid.UUID,
    notice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Admin Endpoint: Remove an obsolete notice.
    """
    service = NoticeService(db)
    async with safe_transaction(db):
        await service.delete_notice(
            admin_user_id=current_user.user_id,
            society_id=society_id,
            notice_id=notice_id,
        )
    return {"success": True, "message": "Notice deleted successfully"}


@router.post(
    "/societies/{society_id}/notices/{notice_id}/read",
    response_model=NoticeReadReceiptResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_notice_read(
    society_id: uuid.UUID,
    notice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_member),
):
    """
    Resident Endpoint: Explicitly mark a notice as read.
    """
    service = NoticeService(db)
    async with safe_transaction(db):
        receipt = await service.mark_as_read(
            society_id=society_id,
            notice_id=notice_id,
            user_id=current_user.user_id,
        )
    return receipt


@router.get(
    "/societies/{society_id}/notices/{notice_id}/receipts",
    response_model=NoticeStatsResponse,
)
async def get_notice_read_stats(
    society_id: uuid.UUID,
    notice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Admin Endpoint: View audit read receipts showing which residents have acknowledged this notice.
    """
    service = NoticeService(db)
    return await service.get_notice_stats(society_id=society_id, notice_id=notice_id)
