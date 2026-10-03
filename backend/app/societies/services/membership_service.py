import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import structlog

from datetime import datetime
from app.core.email_service import EmailService
from app.societies.models import (
    UserSocietyRoleModel,
    UnitResidentModel,
    MembershipStatus,
    SocietyRole,
)
from app.societies import services as services_pkg

logger = structlog.get_logger(__name__)


class MembershipService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = services_pkg.SocietyRepository(db)
        self.user_repo = services_pkg.UserRepository(db)

    async def request_membership(
        self,
        user_id: uuid.UUID,
        society_id: uuid.UUID,
        unit_id: Optional[uuid.UUID] = None,
        role: str = SocietyRole.RESIDENT.value,
    ) -> UserSocietyRoleModel:
        # Verify society exists via repository
        society = await self.repo.get_society(society_id)
        if not society:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found")

        # Verify society has configured units
        units_count = await self.repo.count_units_in_society(society_id)
        if units_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This society is currently in setup mode and has not configured flats yet. Please check back after setup is complete.",
            )

        # Resident / Tenant membership MUST be assigned to a specific unit
        if not unit_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please select your wing and flat number to request membership.",
            )

        # Verify unit via repository
        unit = await self.repo.get_unit(unit_id)
        if not unit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

        # Check existing membership via repository
        existing = await self.repo.get_membership(society_id, user_id)
        if existing:
            if existing.status == MembershipStatus.APPROVED.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You are already an active member of this society",
                )
            elif existing.status == MembershipStatus.PENDING.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Your membership request for this society is already pending approval",
                )
            else:
                # Re-apply for previously rejected membership
                await self.repo.update_membership(
                    existing,
                    status=MembershipStatus.PENDING.value,
                    unit_id=unit_id,
                    role=role,
                )
                return existing

        membership = await self.repo.create_membership(
            user_id=user_id,
            society_id=society_id,
            unit_id=unit_id,
            role=role,
            status=MembershipStatus.PENDING.value,
        )

        logger.info(
            "membership.requested",
            user_id=str(user_id),
            society_id=str(society_id),
            unit_id=str(unit_id) if unit_id else None,
        )
        return membership

    async def get_user_memberships(self, user_id: uuid.UUID) -> List[UserSocietyRoleModel]:
        return await self.repo.list_user_memberships(user_id)

    async def list_pending_requests(self, society_id: uuid.UUID) -> List[UserSocietyRoleModel]:
        return await self.repo.list_pending_memberships(society_id)

    async def approve_membership(
        self, membership_id: uuid.UUID, approved_by_user_id: uuid.UUID
    ) -> UserSocietyRoleModel:
        membership = await self.repo.get_membership_by_id(membership_id)
        if not membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership request not found")

        if not membership.unit_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot approve resident membership without an assigned flat. Please configure society wings and designate a flat first.",
            )

        await self.repo.update_membership(
            membership,
            status=MembershipStatus.APPROVED.value,
            approved_by=approved_by_user_id,
        )

        # Retrieve User, Society, and Unit details via Repository abstraction
        user = await self.user_repo.check_user_exist(membership.user_id)
        society = await self.repo.get_society(membership.society_id)

        unit_number = "N/A"
        if membership.unit_id:
            unit_obj = await self.repo.get_unit(membership.unit_id)
            if unit_obj:
                unit_number = unit_obj.unit_number
                unit_obj.status = "occupied"

            # Check if resident link already exists; if not, create it
            existing_link = await self.repo.get_resident_link(membership.unit_id, membership.user_id)
            if not existing_link:
                res_link = UnitResidentModel(
                    unit_id=membership.unit_id,
                    user_id=membership.user_id,
                    residency_type=membership.role or "resident",
                    is_primary_contact=True,
                    start_date=datetime.now(),
                    status="active",
                )
                self.db.add(res_link)
                await self.db.flush()

        # Fetch primary email via UserRepository
        if user and society:
            credentials = await self.user_repo.get_user_credentials(user.user_id)
            if credentials:
                EmailService.send_membership_approval_email(
                    to_email=credentials[0].identifier,
                    name=f"{user.first_name} {user.last_name}",
                    society_name=society.name,
                    unit_number=unit_number,
                )

        logger.info("membership.approved", membership_id=str(membership_id), user_id=str(membership.user_id))
        return membership

    async def reject_membership(
        self,
        membership_id: uuid.UUID,
        approved_by_user_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> UserSocietyRoleModel:
        membership = await self.repo.get_membership_by_id(membership_id)
        if not membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership request not found")

        await self.repo.update_membership(
            membership,
            status=MembershipStatus.REJECTED.value,
            approved_by=approved_by_user_id,
        )

        user = await self.user_repo.check_user_exist(membership.user_id)
        society = await self.repo.get_society(membership.society_id)

        if user and society:
            credentials = await self.user_repo.get_user_credentials(user.user_id)
            if credentials:
                EmailService.send_membership_rejection_email(
                    to_email=credentials[0].identifier,
                    name=f"{user.first_name} {user.last_name}",
                    society_name=society.name,
                    reason=reason,
                )

        logger.info("membership.rejected", membership_id=str(membership_id), user_id=str(membership.user_id))
        return membership
