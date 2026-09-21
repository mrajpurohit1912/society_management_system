import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import structlog
from fastapi import HTTPException, status

from app.visitors.services.base import BaseVisitorService
from app.visitors.models import VisitorPassModel, VisitorPassStatus
from app.visitors.schemas import VisitorPassCreate

logger = structlog.get_logger(__name__)


class PassService(BaseVisitorService):
    """
    Domain service for resident-created visitor pre-approval passes.
    """

    async def create_visitor_pass(
        self, user_id: uuid.UUID, society_id: uuid.UUID, data: VisitorPassCreate
    ) -> VisitorPassModel:
        society = await self.society_repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Society not found.",
            )

        unit = await self.society_repo.get_unit(data.unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found.",
            )

        # Generate secure 6-digit numeric passcode (100000 - 999999)
        passcode = str(secrets.randbelow(900000) + 100000)
        # Generate cryptographically secure QR token
        qr_token = secrets.token_urlsafe(32)

        valid_from = data.valid_from or datetime.now(timezone.utc)
        valid_until = valid_from + timedelta(hours=data.valid_hours or 12)

        pass_record = VisitorPassModel(
            society_id=society_id,
            unit_id=data.unit_id,
            created_by_user_id=user_id,
            visitor_name=data.visitor_name,
            visitor_phone=data.visitor_phone,
            visitor_type=data.visitor_type,
            passcode=passcode,
            qr_code_token=qr_token,
            valid_from=valid_from,
            valid_until=valid_until,
            status=VisitorPassStatus.ACTIVE.value,
            vehicle_number=data.vehicle_number,
            expected_delivery_company=data.expected_delivery_company,
            notes=data.notes,
        )

        created = await self.visitor_repo.create_pass(pass_record)
        logger.info(
            "visitors.pass_created",
            pass_id=str(created.id),
            society_id=str(society_id),
            unit_id=str(data.unit_id),
            visitor=data.visitor_name,
            type=data.visitor_type,
        )
        return created

    async def list_user_passes(
        self, user_id: uuid.UUID, status_filter: Optional[str] = None
    ) -> List[VisitorPassModel]:
        return await self.visitor_repo.list_passes_by_user(user_id, status=status_filter)

    async def list_unit_passes(
        self, unit_id: uuid.UUID, status_filter: Optional[str] = None
    ) -> List[VisitorPassModel]:
        return await self.visitor_repo.list_passes_by_unit(unit_id, status=status_filter)

    async def get_pass(self, pass_id: uuid.UUID) -> VisitorPassModel:
        pass_record = await self.visitor_repo.get_pass_by_id(pass_id)
        if not pass_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visitor pass not found.",
            )
        return pass_record

    async def revoke_pass(
        self, user_id: uuid.UUID, pass_id: uuid.UUID
    ) -> VisitorPassModel:
        pass_record = await self.get_pass(pass_id)
        if pass_record.created_by_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only revoke visitor passes created by yourself.",
            )

        if pass_record.status != VisitorPassStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot revoke pass with status '{pass_record.status}'.",
            )

        pass_record.status = VisitorPassStatus.REVOKED.value
        updated = await self.visitor_repo.update_pass(pass_record)
        logger.info("visitors.pass_revoked", pass_id=str(pass_id), user_id=str(user_id))
        return updated
