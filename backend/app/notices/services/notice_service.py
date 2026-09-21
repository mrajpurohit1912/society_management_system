import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import structlog
from fastapi import HTTPException, status

from app.notices.services.base import BaseNoticeService
from app.notices.models import (
    NoticeModel,
    NoticeReadReceiptModel,
    NoticeTargetAudience,
)
from app.notices.schemas import (
    NoticeCreate,
    NoticeUpdate,
    NoticeResponse,
)

logger = structlog.get_logger(__name__)


class NoticeService(BaseNoticeService):
    """
    Domain service for digital notice board: publication, target audience segmentation,
    pinning, and audit read receipts.
    """

    async def publish_notice(
        self, user_id: uuid.UUID, society_id: uuid.UUID, payload: NoticeCreate
    ) -> NoticeModel:
        society = await self.society_repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Society not found.",
            )

        if payload.target_building_id:
            building = await self.society_repo.get_building(payload.target_building_id)
            if not building:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target building not found.",
                )

        notice = NoticeModel(
            society_id=society_id,
            created_by_user_id=user_id,
            title=payload.title,
            content=payload.content,
            category=payload.category,
            priority=payload.priority,
            target_audience=payload.target_audience,
            target_building_id=payload.target_building_id,
            is_pinned=payload.is_pinned,
            expires_at=payload.expires_at,
            attachments=payload.attachments,
        )

        saved = await self.notice_repo.create_notice(notice)
        logger.info(
            "notices.published",
            notice_id=str(saved.id),
            society_id=str(society_id),
            title=saved.title,
            target_audience=saved.target_audience,
            priority=saved.priority,
            is_pinned=saved.is_pinned,
        )
        return saved

    async def update_notice(
        self,
        admin_user_id: uuid.UUID,
        society_id: uuid.UUID,
        notice_id: uuid.UUID,
        payload: NoticeUpdate,
    ) -> NoticeModel:
        notice = await self.notice_repo.get_notice_by_id(notice_id)
        if not notice or notice.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notice not found.",
            )

        if payload.title is not None:
            notice.title = payload.title
        if payload.content is not None:
            notice.content = payload.content
        if payload.category is not None:
            notice.category = payload.category
        if payload.priority is not None:
            notice.priority = payload.priority
        if payload.target_audience is not None:
            notice.target_audience = payload.target_audience
        if payload.target_building_id is not None:
            notice.target_building_id = payload.target_building_id
        if payload.is_pinned is not None:
            notice.is_pinned = payload.is_pinned
        if payload.expires_at is not None:
            notice.expires_at = payload.expires_at
        if payload.attachments is not None:
            notice.attachments = payload.attachments

        updated = await self.notice_repo.update_notice(notice)
        logger.info("notices.updated", notice_id=str(notice_id))
        return updated

    async def delete_notice(
        self, admin_user_id: uuid.UUID, society_id: uuid.UUID, notice_id: uuid.UUID
    ) -> None:
        notice = await self.notice_repo.get_notice_by_id(notice_id)
        if not notice or notice.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notice not found.",
            )

        await self.notice_repo.delete_notice(notice)
        logger.info("notices.deleted", notice_id=str(notice_id))

    async def get_notice(
        self, society_id: uuid.UUID, notice_id: uuid.UUID, current_user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        notice = await self.notice_repo.get_notice_by_id(notice_id)
        if not notice or notice.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notice not found.",
            )

        is_read = False
        if current_user_id:
            # Auto-record read receipt upon fetching notice details
            await self.notice_repo.record_read_receipt(notice_id, current_user_id)
            is_read = True

        read_count = await self.notice_repo.get_read_count(notice_id)
        return self._format_notice(notice, read_count=read_count, is_read=is_read)

    async def list_active_notices_for_user(
        self, society_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Lists active notices targeted to this user (society-wide, or building-specific).
        """
        # Determine user's building / residency type from society membership
        membership = await self.society_repo.get_membership(society_id, user_id)
        building_id = None
        residency_type = None

        if membership and membership.unit_id:
            unit = await self.society_repo.get_unit(membership.unit_id)
            if unit and unit.floor_id:
                floor = await self.society_repo.get_floor(unit.floor_id)
                if floor:
                    building_id = floor.building_id

        notices = await self.notice_repo.list_active_notices_for_resident(
            society_id=society_id,
            building_id=building_id,
            residency_type=residency_type,
        )

        results = []
        for n in notices:
            read_count = len(n.read_receipts) if hasattr(n, "read_receipts") and n.read_receipts else 0
            is_read = any(r.user_id == user_id for r in n.read_receipts) if hasattr(n, "read_receipts") and n.read_receipts else False
            results.append(self._format_notice(n, read_count=read_count, is_read=is_read))
        return results

    async def list_all_notices_admin(
        self,
        society_id: uuid.UUID,
        category: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        notices = await self.notice_repo.list_all_notices_admin(
            society_id=society_id, category=category, priority=priority
        )
        results = []
        for n in notices:
            read_count = len(n.read_receipts) if hasattr(n, "read_receipts") and n.read_receipts else 0
            results.append(self._format_notice(n, read_count=read_count, is_read=False))
        return results

    async def mark_as_read(
        self, society_id: uuid.UUID, notice_id: uuid.UUID, user_id: uuid.UUID
    ) -> NoticeReadReceiptModel:
        notice = await self.notice_repo.get_notice_by_id(notice_id)
        if not notice or notice.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notice not found.",
            )
        return await self.notice_repo.record_read_receipt(notice_id, user_id)

    async def get_notice_stats(
        self, society_id: uuid.UUID, notice_id: uuid.UUID
    ) -> Dict[str, Any]:
        notice = await self.notice_repo.get_notice_by_id(notice_id)
        if not notice or notice.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notice not found.",
            )

        read_count = await self.notice_repo.get_read_count(notice_id)
        recent_readers = await self.notice_repo.list_read_receipts(notice_id, limit=50)

        return {
            "notice_id": notice.id,
            "title": notice.title,
            "total_reads": read_count,
            "recent_readers": recent_readers,
        }

    def _format_notice(
        self, notice: NoticeModel, read_count: int = 0, is_read: bool = False
    ) -> Dict[str, Any]:
        return {
            "id": notice.id,
            "society_id": notice.society_id,
            "created_by_user_id": notice.created_by_user_id,
            "title": notice.title,
            "content": notice.content,
            "category": notice.category,
            "priority": notice.priority,
            "target_audience": notice.target_audience,
            "target_building_id": notice.target_building_id,
            "is_pinned": notice.is_pinned,
            "expires_at": notice.expires_at,
            "attachments": notice.attachments,
            "published_at": notice.published_at,
            "created_at": notice.created_at,
            "updated_at": notice.updated_at,
            "read_count": read_count,
            "is_read_by_me": is_read,
        }
