import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.complaints.models import (
    ComplaintTicketModel,
    ComplaintCommentModel,
    ComplaintStatus,
)
from app.authentication.models import UserModel
from app.societies.models import (
    UnitModel,
    FloorModel,
    BuildingModel,
    UserSocietyRoleModel,
    UnitResidentModel,
)


class ComplaintRepository:
    """
    Data access layer for complaint tickets, comments, and helpdesk metrics.
    All database queries use modern async SQLAlchemy 2.0 select semantics.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _eager_load_options(self):
        return [
            selectinload(ComplaintTicketModel.comments),
            selectinload(ComplaintTicketModel.creator).selectinload(UserModel.credentials),
            selectinload(ComplaintTicketModel.unit)
                .selectinload(UnitModel.floor)
                .selectinload(FloorModel.building),
        ]

    async def create_ticket(self, ticket: ComplaintTicketModel) -> ComplaintTicketModel:
        self.db.add(ticket)
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def get_ticket_by_id(self, ticket_id: uuid.UUID) -> Optional[ComplaintTicketModel]:
        query = (
            select(ComplaintTicketModel)
            .where(ComplaintTicketModel.id == ticket_id)
            .options(*self._eager_load_options())
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_ticket_by_number(self, ticket_number: str) -> Optional[ComplaintTicketModel]:
        query = (
            select(ComplaintTicketModel)
            .where(ComplaintTicketModel.ticket_number == ticket_number)
            .options(*self._eager_load_options())
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_ticket(self, ticket: ComplaintTicketModel) -> ComplaintTicketModel:
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def list_tickets_by_society(
        self,
        society_id: uuid.UUID,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        unit_id: Optional[uuid.UUID] = None,
        assigned_to_user_id: Optional[uuid.UUID] = None,
    ) -> List[ComplaintTicketModel]:
        query = (
            select(ComplaintTicketModel)
            .where(ComplaintTicketModel.society_id == society_id)
            .options(*self._eager_load_options())
            .order_by(ComplaintTicketModel.created_at.desc())
        )

        if status:
            query = query.where(ComplaintTicketModel.status == status)
        if priority:
            query = query.where(ComplaintTicketModel.priority == priority)
        if category:
            query = query.where(ComplaintTicketModel.category == category)
        if unit_id:
            query = query.where(ComplaintTicketModel.unit_id == unit_id)
        if assigned_to_user_id:
            query = query.where(ComplaintTicketModel.assigned_to_user_id == assigned_to_user_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_tickets_by_user(
        self,
        society_id: uuid.UUID,
        user_id: uuid.UUID,
        status: Optional[str] = None,
    ) -> List[ComplaintTicketModel]:
        query = (
            select(ComplaintTicketModel)
            .where(
                ComplaintTicketModel.society_id == society_id,
                ComplaintTicketModel.created_by_user_id == user_id,
            )
            .options(*self._eager_load_options())
            .order_by(ComplaintTicketModel.created_at.desc())
        )

        if status:
            query = query.where(ComplaintTicketModel.status == status)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_unit_in_society(
        self, society_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[UnitModel]:
        """Looks up the assigned flat unit for a user in the given society."""
        query_role = (
            select(UnitModel)
            .options(
                selectinload(UnitModel.floor).selectinload(FloorModel.building)
            )
            .join(UserSocietyRoleModel, UserSocietyRoleModel.unit_id == UnitModel.id)
            .where(
                UserSocietyRoleModel.user_id == user_id,
                UserSocietyRoleModel.society_id == society_id,
                UserSocietyRoleModel.unit_id.is_not(None),
            )
        )
        res = await self.db.execute(query_role)
        unit = res.scalars().first()
        if unit:
            return unit

        query_res = (
            select(UnitModel)
            .options(
                selectinload(UnitModel.floor).selectinload(FloorModel.building)
            )
            .join(UnitResidentModel, UnitResidentModel.unit_id == UnitModel.id)
            .join(FloorModel, UnitModel.floor_id == FloorModel.id)
            .join(BuildingModel, FloorModel.building_id == BuildingModel.id)
            .where(
                UnitResidentModel.user_id == user_id,
                BuildingModel.society_id == society_id,
            )
        )
        res2 = await self.db.execute(query_res)
        return res2.scalars().first()

    async def create_comment(self, comment: ComplaintCommentModel) -> ComplaintCommentModel:
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def list_comments(
        self, ticket_id: uuid.UUID, include_internal: bool = False
    ) -> List[ComplaintCommentModel]:
        query = (
            select(ComplaintCommentModel)
            .where(ComplaintCommentModel.ticket_id == ticket_id)
            .order_by(ComplaintCommentModel.created_at.asc())
        )
        if not include_internal:
            query = query.where(ComplaintCommentModel.is_internal.is_(False))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_summary_metrics(self, society_id: uuid.UUID) -> Dict[str, Any]:
        """
        Calculates helpdesk dashboard analytics for a society:
        Counts by status, active overdue SLA tickets, average satisfaction rating,
        and distribution by category.
        """
        now = datetime.now(timezone.utc)

        # Count total and by status
        tickets_query = select(ComplaintTicketModel).where(
            ComplaintTicketModel.society_id == society_id
        )
        result = await self.db.execute(tickets_query)
        tickets = list(result.scalars().all())

        total = len(tickets)
        status_counts = {
            ComplaintStatus.OPEN.value: 0,
            ComplaintStatus.ASSIGNED.value: 0,
            ComplaintStatus.IN_PROGRESS.value: 0,
            ComplaintStatus.RESOLVED.value: 0,
            ComplaintStatus.CLOSED.value: 0,
        }
        category_counts: Dict[str, int] = {}
        overdue_count = 0
        ratings: List[int] = []

        for t in tickets:
            # Status counts
            if t.status in status_counts:
                status_counts[t.status] += 1

            # Category breakdown
            category_counts[t.category] = category_counts.get(t.category, 0) + 1

            # SLA breach tracking: active ticket past its SLA deadline
            if t.status in (
                ComplaintStatus.OPEN.value,
                ComplaintStatus.ASSIGNED.value,
                ComplaintStatus.IN_PROGRESS.value,
            ):
                sla_deadline = t.sla_deadline
                # Ensure timezone-aware comparison
                if sla_deadline.tzinfo is None:
                    sla_deadline = sla_deadline.replace(tzinfo=timezone.utc)
                if now > sla_deadline:
                    overdue_count += 1

            # Rating accumulation
            if t.resident_rating is not None:
                ratings.append(t.resident_rating)

        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

        return {
            "total_tickets": total,
            "open_tickets": status_counts[ComplaintStatus.OPEN.value],
            "assigned_tickets": status_counts[ComplaintStatus.ASSIGNED.value],
            "in_progress_tickets": status_counts[ComplaintStatus.IN_PROGRESS.value],
            "resolved_tickets": status_counts[ComplaintStatus.RESOLVED.value],
            "closed_tickets": status_counts[ComplaintStatus.CLOSED.value],
            "overdue_sla_tickets": overdue_count,
            "average_rating": avg_rating,
            "by_category": category_counts,
        }
