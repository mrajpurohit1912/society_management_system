import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.notices.models import (
    NoticeModel,
    NoticeReadReceiptModel,
    NoticeTargetAudience,
)


class NoticeRepository:
    """
    Data access layer for digital notice board, audience segmentation,
    and read receipt tracking.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notice(self, notice: NoticeModel) -> NoticeModel:
        self.db.add(notice)
        await self.db.flush()
        await self.db.refresh(notice)
        return notice

    async def get_notice_by_id(self, notice_id: uuid.UUID) -> Optional[NoticeModel]:
        query = (
            select(NoticeModel)
            .where(NoticeModel.id == notice_id)
            .options(selectinload(NoticeModel.read_receipts))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_notice(self, notice: NoticeModel) -> NoticeModel:
        await self.db.flush()
        await self.db.refresh(notice)
        return notice

    async def delete_notice(self, notice: NoticeModel) -> None:
        await self.db.delete(notice)
        await self.db.flush()

    async def list_active_notices_for_resident(
        self,
        society_id: uuid.UUID,
        building_id: Optional[uuid.UUID] = None,
        residency_type: Optional[str] = None,
    ) -> List[NoticeModel]:
        """
        Fetches unexpired notices targeted to this resident:
        Ordered with pinned notices first, then newest published notices.
        """
        now = datetime.now(timezone.utc)
        query = (
            select(NoticeModel)
            .where(
                NoticeModel.society_id == society_id,
                or_(NoticeModel.expires_at.is_(None), NoticeModel.expires_at > now),
            )
            .options(selectinload(NoticeModel.read_receipts))
            .order_by(NoticeModel.is_pinned.desc(), NoticeModel.published_at.desc())
        )

        # Audience segmentation filter
        audience_conditions = [NoticeModel.target_audience == NoticeTargetAudience.ALL.value]
        if building_id:
            audience_conditions.append(
                and_(
                    NoticeModel.target_audience == NoticeTargetAudience.BUILDING.value,
                    NoticeModel.target_building_id == building_id,
                )
            )
        if residency_type:
            if "owner" in residency_type.lower():
                audience_conditions.append(
                    NoticeModel.target_audience == NoticeTargetAudience.OWNERS_ONLY.value
                )
            elif "tenant" in residency_type.lower():
                audience_conditions.append(
                    NoticeModel.target_audience == NoticeTargetAudience.TENANTS_ONLY.value
                )

        query = query.where(or_(*audience_conditions))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all_notices_admin(
        self,
        society_id: uuid.UUID,
        category: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[NoticeModel]:
        """
        Admin query returning all active and archived notices for society.
        """
        query = (
            select(NoticeModel)
            .where(NoticeModel.society_id == society_id)
            .options(selectinload(NoticeModel.read_receipts))
            .order_by(NoticeModel.is_pinned.desc(), NoticeModel.published_at.desc())
        )
        if category:
            query = query.where(NoticeModel.category == category)
        if priority:
            query = query.where(NoticeModel.priority == priority)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def record_read_receipt(
        self, notice_id: uuid.UUID, user_id: uuid.UUID
    ) -> NoticeReadReceiptModel:
        """
        Records that a user has read the notice. Idempotent.
        """
        query = select(NoticeReadReceiptModel).where(
            NoticeReadReceiptModel.notice_id == notice_id,
            NoticeReadReceiptModel.user_id == user_id,
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        receipt = NoticeReadReceiptModel(notice_id=notice_id, user_id=user_id)
        self.db.add(receipt)
        await self.db.flush()
        await self.db.refresh(receipt)
        return receipt

    async def is_read_by_user(self, notice_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        query = select(NoticeReadReceiptModel.id).where(
            NoticeReadReceiptModel.notice_id == notice_id,
            NoticeReadReceiptModel.user_id == user_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_read_count(self, notice_id: uuid.UUID) -> int:
        query = select(func.count(NoticeReadReceiptModel.id)).where(
            NoticeReadReceiptModel.notice_id == notice_id
        )
        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def list_read_receipts(
        self, notice_id: uuid.UUID, limit: int = 50
    ) -> List[NoticeReadReceiptModel]:
        query = (
            select(NoticeReadReceiptModel)
            .where(NoticeReadReceiptModel.notice_id == notice_id)
            .order_by(NoticeReadReceiptModel.read_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
