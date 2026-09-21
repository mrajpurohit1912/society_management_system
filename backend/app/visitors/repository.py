import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.visitors.models import (
    VisitorPassModel,
    VisitorLogModel,
    VisitorPassStatus,
    VisitorLogStatus,
    VisitorType,
)


class VisitorRepository:
    """
    Data Access Layer (Repository Pattern) for Visitor & Gatekeeper Management.
    Encapsulates all database queries using SQLAlchemy 2.0 Async Session.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------
    # Visitor Passes
    # ---------------------------------------------------------

    async def create_pass(self, pass_record: VisitorPassModel) -> VisitorPassModel:
        self.db.add(pass_record)
        await self.db.flush()
        return pass_record

    async def get_pass_by_id(self, pass_id: uuid.UUID) -> Optional[VisitorPassModel]:
        stmt = (
            select(VisitorPassModel)
            .where(VisitorPassModel.id == pass_id)
            .options(
                selectinload(VisitorPassModel.unit),
                selectinload(VisitorPassModel.creator),
                selectinload(VisitorPassModel.logs),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_valid_pass_by_code(
        self, society_id: uuid.UUID, passcode: str
    ) -> Optional[VisitorPassModel]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(VisitorPassModel)
            .where(
                VisitorPassModel.society_id == society_id,
                VisitorPassModel.passcode == passcode,
                VisitorPassModel.status == VisitorPassStatus.ACTIVE.value,
                VisitorPassModel.valid_from <= now,
                VisitorPassModel.valid_until >= now,
            )
            .options(
                selectinload(VisitorPassModel.unit),
                selectinload(VisitorPassModel.creator),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_valid_pass_by_qr(
        self, society_id: uuid.UUID, qr_token: str
    ) -> Optional[VisitorPassModel]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(VisitorPassModel)
            .where(
                VisitorPassModel.society_id == society_id,
                VisitorPassModel.qr_code_token == qr_token,
                VisitorPassModel.status == VisitorPassStatus.ACTIVE.value,
                VisitorPassModel.valid_from <= now,
                VisitorPassModel.valid_until >= now,
            )
            .options(
                selectinload(VisitorPassModel.unit),
                selectinload(VisitorPassModel.creator),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_passes_by_user(
        self, user_id: uuid.UUID, status: Optional[str] = None
    ) -> List[VisitorPassModel]:
        stmt = (
            select(VisitorPassModel)
            .where(VisitorPassModel.created_by_user_id == user_id)
            .order_by(VisitorPassModel.created_at.desc())
        )
        if status:
            stmt = stmt.where(VisitorPassModel.status == status)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_passes_by_unit(
        self, unit_id: uuid.UUID, status: Optional[str] = None
    ) -> List[VisitorPassModel]:
        stmt = (
            select(VisitorPassModel)
            .where(VisitorPassModel.unit_id == unit_id)
            .order_by(VisitorPassModel.created_at.desc())
        )
        if status:
            stmt = stmt.where(VisitorPassModel.status == status)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_passes_by_society(
        self, society_id: uuid.UUID, status: Optional[str] = None
    ) -> List[VisitorPassModel]:
        stmt = (
            select(VisitorPassModel)
            .where(VisitorPassModel.society_id == society_id)
            .order_by(VisitorPassModel.created_at.desc())
        )
        if status:
            stmt = stmt.where(VisitorPassModel.status == status)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_pass(self, pass_record: VisitorPassModel) -> VisitorPassModel:
        await self.db.flush()
        return pass_record

    # ---------------------------------------------------------
    # Visitor Logs
    # ---------------------------------------------------------

    async def create_log(self, log_record: VisitorLogModel) -> VisitorLogModel:
        self.db.add(log_record)
        await self.db.flush()
        return log_record

    async def get_log_by_id(self, log_id: uuid.UUID) -> Optional[VisitorLogModel]:
        stmt = (
            select(VisitorLogModel)
            .where(VisitorLogModel.id == log_id)
            .options(
                selectinload(VisitorLogModel.unit),
                selectinload(VisitorLogModel.pass_record),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_active_log_by_pass_id(
        self, pass_id: uuid.UUID
    ) -> Optional[VisitorLogModel]:
        stmt = select(VisitorLogModel).where(
            VisitorLogModel.pass_id == pass_id,
            VisitorLogModel.status == VisitorLogStatus.INSIDE.value,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_active_visitors_by_society(
        self, society_id: uuid.UUID
    ) -> List[VisitorLogModel]:
        stmt = (
            select(VisitorLogModel)
            .where(
                VisitorLogModel.society_id == society_id,
                VisitorLogModel.status == VisitorLogStatus.INSIDE.value,
            )
            .order_by(VisitorLogModel.check_in_time.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_logs_by_society(
        self,
        society_id: uuid.UUID,
        status: Optional[str] = None,
        visitor_type: Optional[str] = None,
        unit_id: Optional[uuid.UUID] = None,
    ) -> List[VisitorLogModel]:
        stmt = (
            select(VisitorLogModel)
            .where(VisitorLogModel.society_id == society_id)
            .order_by(VisitorLogModel.check_in_time.desc())
        )
        if status:
            stmt = stmt.where(VisitorLogModel.status == status)
        if visitor_type:
            stmt = stmt.where(VisitorLogModel.visitor_type == visitor_type)
        if unit_id:
            stmt = stmt.where(VisitorLogModel.unit_id == unit_id)

        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_log(self, log_record: VisitorLogModel) -> VisitorLogModel:
        await self.db.flush()
        return log_record

    # ---------------------------------------------------------
    # Analytics & Summary
    # ---------------------------------------------------------

    async def get_active_visitors_summary(
        self, society_id: uuid.UUID
    ) -> Dict[str, int]:
        total_inside = await self.db.scalar(
            select(func.count(VisitorLogModel.id)).where(
                VisitorLogModel.society_id == society_id,
                VisitorLogModel.status == VisitorLogStatus.INSIDE.value,
            )
        ) or 0

        deliveries = await self.db.scalar(
            select(func.count(VisitorLogModel.id)).where(
                VisitorLogModel.society_id == society_id,
                VisitorLogModel.status == VisitorLogStatus.INSIDE.value,
                VisitorLogModel.visitor_type == VisitorType.DELIVERY.value,
            )
        ) or 0

        cabs = await self.db.scalar(
            select(func.count(VisitorLogModel.id)).where(
                VisitorLogModel.society_id == society_id,
                VisitorLogModel.status == VisitorLogStatus.INSIDE.value,
                VisitorLogModel.visitor_type == VisitorType.CAB.value,
            )
        ) or 0

        guests = await self.db.scalar(
            select(func.count(VisitorLogModel.id)).where(
                VisitorLogModel.society_id == society_id,
                VisitorLogModel.status == VisitorLogStatus.INSIDE.value,
                VisitorLogModel.visitor_type == VisitorType.GUEST.value,
            )
        ) or 0

        services = await self.db.scalar(
            select(func.count(VisitorLogModel.id)).where(
                VisitorLogModel.society_id == society_id,
                VisitorLogModel.status == VisitorLogStatus.INSIDE.value,
                VisitorLogModel.visitor_type == VisitorType.SERVICE.value,
            )
        ) or 0

        # Overstay threshold: visitors inside for > 4 hours
        overstay_cutoff = datetime.now(timezone.utc) - timedelta(hours=4)
        overstay = await self.db.scalar(
            select(func.count(VisitorLogModel.id)).where(
                VisitorLogModel.society_id == society_id,
                VisitorLogModel.status == VisitorLogStatus.INSIDE.value,
                VisitorLogModel.check_in_time <= overstay_cutoff,
            )
        ) or 0

        return {
            "total_inside": int(total_inside),
            "deliveries_inside": int(deliveries),
            "cabs_inside": int(cabs),
            "guests_inside": int(guests),
            "services_inside": int(services),
            "overstay_count": int(overstay),
        }
