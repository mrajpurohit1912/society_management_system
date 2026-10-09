import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import structlog
from fastapi import HTTPException, status

from app.complaints.services.base import BaseComplaintService
from app.complaints.models import (
    ComplaintTicketModel,
    ComplaintCommentModel,
    ComplaintStatus,
    SLA_HOURS_MAP,
)
from app.complaints.schemas import (
    ComplaintCreate,
    ComplaintAssignRequest,
    ComplaintStatusUpdateRequest,
    ComplaintResolveRequest,
    ComplaintCloseRequest,
    ComplaintCommentCreate,
)

logger = structlog.get_logger(__name__)


class ComplaintService(BaseComplaintService):
    """
    Domain service implementing the Helpdesk & Service Request lifecycle:
    Creation -> Automated SLA Calculation -> Assignment -> In Progress ->
    Resolution -> Closure & Resident Feedback.
    """

    async def create_complaint(
        self, user_id: uuid.UUID, society_id: uuid.UUID, payload: ComplaintCreate
    ) -> ComplaintTicketModel:
        society = await self.society_repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Society not found.",
            )

        unit_id = payload.unit_id
        if not unit_id:
            user_unit = await self.complaint_repo.get_user_unit_in_society(society_id, user_id)
            if user_unit:
                unit_id = user_unit.id
        else:
            unit = await self.society_repo.get_unit(unit_id)
            if not unit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Unit not found.",
                )

        # Generate unique human-readable ticket number (e.g., TKT-2026-F3A1)
        current_year = datetime.now(timezone.utc).year
        unique_suffix = secrets.token_hex(3).upper()
        ticket_number = f"TKT-{current_year}-{unique_suffix}"

        # Calculate SLA deadline based on priority (P1: 4h, P2: 24h, P3: 48h, P4: 72h)
        sla_hours = SLA_HOURS_MAP.get(payload.priority, 48)
        now = datetime.now(timezone.utc)
        sla_deadline = now + timedelta(hours=sla_hours)

        ticket = ComplaintTicketModel(
            society_id=society_id,
            unit_id=unit_id,
            created_by_user_id=user_id,
            ticket_number=ticket_number,
            title=payload.title,
            description=payload.description,
            category=payload.category,
            scope=payload.scope,
            priority=payload.priority,
            status=ComplaintStatus.OPEN.value,
            common_area_location=payload.common_area_location,
            photos=payload.photos,
            sla_deadline=sla_deadline,
        )

        saved = await self.complaint_repo.create_ticket(ticket)
        logger.info(
            "complaints.ticket_created",
            ticket_id=str(saved.id),
            ticket_number=saved.ticket_number,
            society_id=str(society_id),
            priority=saved.priority,
            sla_deadline=sla_deadline.isoformat(),
        )
        return saved

    async def assign_complaint(
        self,
        admin_user_id: uuid.UUID,
        society_id: uuid.UUID,
        ticket_id: uuid.UUID,
        payload: ComplaintAssignRequest,
    ) -> ComplaintTicketModel:
        ticket = await self.complaint_repo.get_ticket_by_id(ticket_id)
        if not ticket or ticket.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint ticket not found.",
            )

        if payload.assigned_to_user_id:
            user = await self.user_repo.check_user_exist(payload.assigned_to_user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assigned staff user not found.",
                )
            ticket.assigned_to_user_id = payload.assigned_to_user_id

        if payload.assigned_vendor_name:
            ticket.assigned_vendor_name = payload.assigned_vendor_name
        if payload.assigned_vendor_phone:
            ticket.assigned_vendor_phone = payload.assigned_vendor_phone

        ticket.status = ComplaintStatus.ASSIGNED.value
        ticket.assigned_at = datetime.now(timezone.utc)

        # Record assignment note as comment if provided
        if payload.notes:
            comment = ComplaintCommentModel(
                ticket_id=ticket.id,
                user_id=admin_user_id,
                comment=f"Assigned to {payload.assigned_vendor_name or 'staff member'}. Note: {payload.notes}",
                is_internal=False,
            )
            await self.complaint_repo.create_comment(comment)

        updated = await self.complaint_repo.update_ticket(ticket)
        logger.info(
            "complaints.ticket_assigned",
            ticket_id=str(ticket.id),
            assigned_to=str(ticket.assigned_to_user_id),
            vendor=ticket.assigned_vendor_name,
        )
        return updated

    async def update_status(
        self,
        admin_user_id: uuid.UUID,
        society_id: uuid.UUID,
        ticket_id: uuid.UUID,
        payload: ComplaintStatusUpdateRequest,
    ) -> ComplaintTicketModel:
        ticket = await self.complaint_repo.get_ticket_by_id(ticket_id)
        if not ticket or ticket.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint ticket not found.",
            )

        ticket.status = payload.status
        if payload.notes:
            comment = ComplaintCommentModel(
                ticket_id=ticket.id,
                user_id=admin_user_id,
                comment=f"Status updated to '{payload.status}'. Note: {payload.notes}",
                is_internal=False,
            )
            await self.complaint_repo.create_comment(comment)

        updated = await self.complaint_repo.update_ticket(ticket)
        logger.info("complaints.status_updated", ticket_id=str(ticket.id), status=payload.status)
        return updated

    async def resolve_complaint(
        self,
        admin_user_id: uuid.UUID,
        society_id: uuid.UUID,
        ticket_id: uuid.UUID,
        payload: ComplaintResolveRequest,
    ) -> ComplaintTicketModel:
        ticket = await self.complaint_repo.get_ticket_by_id(ticket_id)
        if not ticket or ticket.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint ticket not found.",
            )

        ticket.status = ComplaintStatus.RESOLVED.value
        ticket.resolved_at = datetime.now(timezone.utc)
        ticket.resolution_notes = payload.resolution_notes
        if payload.resolution_photos:
            ticket.resolution_photos = payload.resolution_photos

        # Add resolution note as public comment
        comment = ComplaintCommentModel(
            ticket_id=ticket.id,
            user_id=admin_user_id,
            comment=f"Issue Resolved: {payload.resolution_notes}",
            is_internal=False,
        )
        await self.complaint_repo.create_comment(comment)

        updated = await self.complaint_repo.update_ticket(ticket)
        logger.info("complaints.ticket_resolved", ticket_id=str(ticket.id))
        return updated

    async def close_complaint(
        self,
        resident_user_id: uuid.UUID,
        society_id: uuid.UUID,
        ticket_id: uuid.UUID,
        payload: ComplaintCloseRequest,
    ) -> ComplaintTicketModel:
        ticket = await self.complaint_repo.get_ticket_by_id(ticket_id)
        if not ticket or ticket.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint ticket not found.",
            )

        if ticket.created_by_user_id != resident_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the resident who reported the issue can close it and provide feedback.",
            )

        if ticket.status != ComplaintStatus.RESOLVED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot close ticket with status '{ticket.status}'. Ticket must be resolved first.",
            )

        ticket.status = ComplaintStatus.CLOSED.value
        ticket.closed_at = datetime.now(timezone.utc)
        ticket.resident_rating = payload.resident_rating
        ticket.resident_feedback = payload.resident_feedback

        updated = await self.complaint_repo.update_ticket(ticket)
        logger.info(
            "complaints.ticket_closed",
            ticket_id=str(ticket.id),
            rating=payload.resident_rating,
        )
        return updated

    async def add_comment(
        self,
        user_id: uuid.UUID,
        society_id: uuid.UUID,
        ticket_id: uuid.UUID,
        payload: ComplaintCommentCreate,
    ) -> ComplaintCommentModel:
        ticket = await self.complaint_repo.get_ticket_by_id(ticket_id)
        if not ticket or ticket.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint ticket not found.",
            )

        comment = ComplaintCommentModel(
            ticket_id=ticket.id,
            user_id=user_id,
            comment=payload.comment,
            is_internal=payload.is_internal,
            attachment_url=payload.attachment_url,
        )
        return await self.complaint_repo.create_comment(comment)

    async def list_comments(
        self, society_id: uuid.UUID, ticket_id: uuid.UUID, include_internal: bool = False
    ) -> List[ComplaintCommentModel]:
        ticket = await self.complaint_repo.get_ticket_by_id(ticket_id)
        if not ticket or ticket.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint ticket not found.",
            )
        return await self.complaint_repo.list_comments(ticket_id, include_internal=include_internal)

    async def get_complaint(
        self, society_id: uuid.UUID, ticket_id: uuid.UUID
    ) -> Dict[str, Any]:
        ticket = await self.complaint_repo.get_ticket_by_id(ticket_id)
        if not ticket or ticket.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint ticket not found.",
            )
        fallback_unit = None
        if not ticket.unit:
            fallback_unit = await self.complaint_repo.get_user_unit_in_society(
                society_id, ticket.created_by_user_id
            )
        return self._format_ticket(ticket, fallback_unit=fallback_unit)

    async def list_complaints(
        self,
        society_id: uuid.UUID,
        status_filter: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        unit_id: Optional[uuid.UUID] = None,
        assigned_to_user_id: Optional[uuid.UUID] = None,
    ) -> List[Dict[str, Any]]:
        tickets = await self.complaint_repo.list_tickets_by_society(
            society_id=society_id,
            status=status_filter,
            priority=priority,
            category=category,
            unit_id=unit_id,
            assigned_to_user_id=assigned_to_user_id,
        )
        fallback_units: Dict[uuid.UUID, Any] = {}
        for t in tickets:
            if not t.unit and t.created_by_user_id not in fallback_units:
                fallback_units[t.created_by_user_id] = await self.complaint_repo.get_user_unit_in_society(
                    society_id, t.created_by_user_id
                )
        return [
            self._format_ticket(t, fallback_unit=fallback_units.get(t.created_by_user_id))
            for t in tickets
        ]

    async def list_user_complaints(
        self, society_id: uuid.UUID, user_id: uuid.UUID, status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        tickets = await self.complaint_repo.list_tickets_by_user(
            society_id=society_id, user_id=user_id, status=status_filter
        )
        user_unit = None
        if any(not t.unit for t in tickets):
            user_unit = await self.complaint_repo.get_user_unit_in_society(society_id, user_id)
        return [self._format_ticket(t, fallback_unit=user_unit) for t in tickets]

    async def get_summary_metrics(self, society_id: uuid.UUID) -> Dict[str, Any]:
        return await self.complaint_repo.get_summary_metrics(society_id)

    def _format_ticket(
        self, ticket: ComplaintTicketModel, fallback_unit: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Maps ticket to dictionary with calculated is_overdue SLA flag and resident/unit details."""
        now = datetime.now(timezone.utc)
        sla_deadline = ticket.sla_deadline
        if sla_deadline.tzinfo is None:
            sla_deadline = sla_deadline.replace(tzinfo=timezone.utc)

        is_overdue = (
            ticket.status not in (ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value)
            and now > sla_deadline
        )

        comments_count = len(ticket.comments) if hasattr(ticket, "comments") and ticket.comments else 0

        # Unit context
        unit_obj = ticket.unit or fallback_unit
        unit_number = unit_obj.unit_number if unit_obj else None
        floor_number = (
            unit_obj.floor.floor_number
            if (unit_obj and hasattr(unit_obj, "floor") and unit_obj.floor)
            else None
        )
        building_name = (
            unit_obj.floor.building.name
            if (
                unit_obj
                and hasattr(unit_obj, "floor")
                and unit_obj.floor
                and hasattr(unit_obj.floor, "building")
                and unit_obj.floor.building
            )
            else None
        )

        # Creator / Resident details
        creator_name = (
            f"{ticket.creator.first_name} {ticket.creator.last_name}".strip()
            if hasattr(ticket, "creator") and ticket.creator
            else None
        )
        creator_email = None
        creator_phone = None
        if hasattr(ticket, "creator") and ticket.creator and hasattr(ticket.creator, "credentials") and ticket.creator.credentials:
            for cred in ticket.creator.credentials:
                if not creator_email and (cred.provider in ("email", "google") or "@" in cred.identifier):
                    creator_email = cred.identifier
                elif not creator_phone and (
                    cred.provider == "phone"
                    or (not "@" in cred.identifier and cred.identifier.replace("+", "").replace(" ", "").isdigit())
                ):
                    creator_phone = cred.identifier
            if not creator_email and not creator_phone and ticket.creator.credentials:
                first_cred = ticket.creator.credentials[0].identifier
                if "@" in first_cred:
                    creator_email = first_cred
                else:
                    creator_phone = first_cred

        return {
            "id": ticket.id,
            "society_id": ticket.society_id,
            "unit_id": ticket.unit_id or (unit_obj.id if unit_obj else None),
            "created_by_user_id": ticket.created_by_user_id,
            "ticket_number": ticket.ticket_number,
            "title": ticket.title,
            "description": ticket.description,
            "category": ticket.category,
            "scope": ticket.scope,
            "priority": ticket.priority,
            "status": ticket.status,
            "common_area_location": ticket.common_area_location,
            "photos": ticket.photos,
            "sla_deadline": ticket.sla_deadline,
            "is_overdue": is_overdue,
            "assigned_to_user_id": ticket.assigned_to_user_id,
            "assigned_vendor_name": ticket.assigned_vendor_name,
            "assigned_vendor_phone": ticket.assigned_vendor_phone,
            "assigned_at": ticket.assigned_at,
            "resolved_at": ticket.resolved_at,
            "closed_at": ticket.closed_at,
            "resolution_notes": ticket.resolution_notes,
            "resolution_photos": ticket.resolution_photos,
            "resident_rating": ticket.resident_rating,
            "resident_feedback": ticket.resident_feedback,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "comments_count": comments_count,
            "creator_name": creator_name,
            "creator_email": creator_email,
            "creator_phone": creator_phone,
            "unit_number": unit_number,
            "building_name": building_name,
            "floor_number": floor_number,
        }
