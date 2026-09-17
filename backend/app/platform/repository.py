import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.societies.models import SocietyLeadModel, SubscriptionModel, SocietyModel
from app.authentication.models import UserModel


class PlatformRepository:
    """
    Data Access Layer (Repository Pattern) for Platform Administration & Leads.
    Encapsulates all database operations using SQLAlchemy 2.0 Async Session.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_lead(self, lead: SocietyLeadModel) -> SocietyLeadModel:
        """Persist a new society lead."""
        self.db.add(lead)
        await self.db.flush()
        return lead

    async def list_leads(self, status_filter: Optional[str] = None) -> List[SocietyLeadModel]:
        """Fetch leads ordered by creation date descending, with optional status filter."""
        stmt = select(SocietyLeadModel).order_by(SocietyLeadModel.created_at.desc())
        if status_filter:
            stmt = stmt.where(SocietyLeadModel.status == status_filter)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_lead_by_id(self, lead_id: uuid.UUID) -> Optional[SocietyLeadModel]:
        """Fetch a specific society lead by ID."""
        stmt = select(SocietyLeadModel).where(SocietyLeadModel.id == lead_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def update_lead(self, lead: SocietyLeadModel) -> SocietyLeadModel:
        """Flush changes on a tracked lead instance."""
        await self.db.flush()
        return lead

    async def create_subscription(self, subscription: SubscriptionModel) -> SubscriptionModel:
        """Persist a new society subscription."""
        self.db.add(subscription)
        await self.db.flush()
        return subscription

    async def get_subscription_by_society_id(self, society_id: uuid.UUID) -> Optional[SubscriptionModel]:
        """Fetch subscription record for a society."""
        stmt = select(SubscriptionModel).where(SubscriptionModel.society_id == society_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_dashboard_metrics(self) -> Dict[str, int]:
        """Compute high-level platform aggregate metrics."""
        soc_count = await self.db.scalar(select(func.count(SocietyModel.id)))
        sub_count = await self.db.scalar(
            select(func.count(SubscriptionModel.id)).where(SubscriptionModel.status == "active")
        )
        user_count = await self.db.scalar(select(func.count(UserModel.user_id)))
        lead_count = await self.db.scalar(select(func.count(SocietyLeadModel.id)))

        return {
            "total_societies": soc_count or 0,
            "active_subscriptions": sub_count or 0,
            "total_users": user_count or 0,
            "total_leads": lead_count or 0,
        }
