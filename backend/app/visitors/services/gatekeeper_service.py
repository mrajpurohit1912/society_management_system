import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import structlog
from fastapi import HTTPException, status

from app.visitors.services.base import BaseVisitorService
from app.visitors.models import (
    VisitorLogModel,
    VisitorPassStatus,
    VisitorLogStatus,
    EntryType,
)
from app.visitors.schemas import (
    PasscodeCheckInRequest,
    QRCheckInRequest,
    QuickCheckInRequest,
    CheckOutRequest,
)

logger = structlog.get_logger(__name__)


class GatekeeperService(BaseVisitorService):
    """
    Domain service for security gate operations: passcode/QR check-in,
    instant delivery/cab check-in, and visitor checkout.
    """

    async def verify_and_checkin_passcode(
        self, guard_id: Optional[uuid.UUID], society_id: uuid.UUID, payload: PasscodeCheckInRequest
    ) -> VisitorLogModel:
        pass_record = await self.visitor_repo.get_valid_pass_by_code(
            society_id=society_id, passcode=payload.passcode
        )
        if not pass_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid, expired, or revoked visitor passcode.",
            )

        active_log = await self.visitor_repo.get_active_log_by_pass_id(pass_record.id)
        if active_log:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Visitor with this pass is already checked in and currently inside.",
            )

        log_record = VisitorLogModel(
            society_id=society_id,
            unit_id=pass_record.unit_id,
            pass_id=pass_record.id,
            visitor_name=pass_record.visitor_name,
            visitor_phone=pass_record.visitor_phone,
            visitor_type=pass_record.visitor_type,
            entry_type=EntryType.PRE_APPROVED.value,
            status=VisitorLogStatus.INSIDE.value,
            vehicle_number=pass_record.vehicle_number,
            company_name=pass_record.expected_delivery_company,
            gate_number=payload.gate_number,
            checked_in_by=guard_id,
        )
        saved_log = await self.visitor_repo.create_log(log_record)

        # Mark one-time pass as COMPLETED
        pass_record.status = VisitorPassStatus.COMPLETED.value
        await self.visitor_repo.update_pass(pass_record)

        logger.info(
            "visitors.passcode_checkin_success",
            log_id=str(saved_log.id),
            pass_id=str(pass_record.id),
            society_id=str(society_id),
            visitor=pass_record.visitor_name,
        )
        return saved_log

    async def verify_and_checkin_qr(
        self, guard_id: Optional[uuid.UUID], society_id: uuid.UUID, payload: QRCheckInRequest
    ) -> VisitorLogModel:
        pass_record = await self.visitor_repo.get_valid_pass_by_qr(
            society_id=society_id, qr_token=payload.qr_token
        )
        if not pass_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid, expired, or revoked visitor QR code.",
            )

        active_log = await self.visitor_repo.get_active_log_by_pass_id(pass_record.id)
        if active_log:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Visitor with this pass is already checked in and currently inside.",
            )

        log_record = VisitorLogModel(
            society_id=society_id,
            unit_id=pass_record.unit_id,
            pass_id=pass_record.id,
            visitor_name=pass_record.visitor_name,
            visitor_phone=pass_record.visitor_phone,
            visitor_type=pass_record.visitor_type,
            entry_type=EntryType.PRE_APPROVED.value,
            status=VisitorLogStatus.INSIDE.value,
            vehicle_number=pass_record.vehicle_number,
            company_name=pass_record.expected_delivery_company,
            gate_number=payload.gate_number,
            checked_in_by=guard_id,
        )
        saved_log = await self.visitor_repo.create_log(log_record)

        pass_record.status = VisitorPassStatus.COMPLETED.value
        await self.visitor_repo.update_pass(pass_record)

        logger.info(
            "visitors.qr_checkin_success",
            log_id=str(saved_log.id),
            pass_id=str(pass_record.id),
            society_id=str(society_id),
            visitor=pass_record.visitor_name,
        )
        return saved_log

    async def quick_checkin(
        self, guard_id: Optional[uuid.UUID], society_id: uuid.UUID, payload: QuickCheckInRequest
    ) -> VisitorLogModel:
        unit = await self.society_repo.get_unit(payload.unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found.",
            )

        log_record = VisitorLogModel(
            society_id=society_id,
            unit_id=payload.unit_id,
            pass_id=None,
            visitor_name=payload.visitor_name,
            visitor_phone=payload.visitor_phone,
            visitor_type=payload.visitor_type,
            entry_type=EntryType.QUICK_CHECKIN.value,
            status=VisitorLogStatus.INSIDE.value,
            company_name=payload.company_name,
            vehicle_number=payload.vehicle_number,
            gate_number=payload.gate_number,
            checked_in_by=guard_id,
        )
        saved_log = await self.visitor_repo.create_log(log_record)

        logger.info(
            "visitors.quick_checkin_logged",
            log_id=str(saved_log.id),
            society_id=str(society_id),
            unit_id=str(payload.unit_id),
            type=payload.visitor_type,
            company=payload.company_name,
        )
        return saved_log

    async def checkout_visitor(
        self, guard_id: Optional[uuid.UUID], society_id: uuid.UUID, log_id: uuid.UUID, payload: CheckOutRequest
    ) -> VisitorLogModel:
        log_record = await self.visitor_repo.get_log_by_id(log_id)
        if not log_record or log_record.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visitor entry log not found for this society.",
            )

        if log_record.status != VisitorLogStatus.INSIDE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Visitor is not currently inside (status: '{log_record.status}').",
            )

        log_record.status = VisitorLogStatus.CHECKED_OUT.value
        log_record.check_out_time = datetime.now(timezone.utc)
        log_record.checked_out_by = guard_id
        if payload.gate_number:
            log_record.gate_number = payload.gate_number

        updated = await self.visitor_repo.update_log(log_record)
        logger.info(
            "visitors.checkout_completed",
            log_id=str(log_id),
            society_id=str(society_id),
            visitor=log_record.visitor_name,
        )
        return updated

    async def list_active_visitors(self, society_id: uuid.UUID) -> List[VisitorLogModel]:
        return await self.visitor_repo.list_active_visitors_by_society(society_id)

    async def list_visitor_logs(
        self,
        society_id: uuid.UUID,
        status_filter: Optional[str] = None,
        visitor_type: Optional[str] = None,
        unit_id: Optional[uuid.UUID] = None,
    ) -> List[VisitorLogModel]:
        return await self.visitor_repo.list_logs_by_society(
            society_id=society_id,
            status=status_filter,
            visitor_type=visitor_type,
            unit_id=unit_id,
        )

    async def get_active_summary(self, society_id: uuid.UUID) -> Dict[str, int]:
        return await self.visitor_repo.get_active_visitors_summary(society_id)
