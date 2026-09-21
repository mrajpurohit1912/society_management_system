import uuid
from typing import Optional, List
import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.authentication.dependencies import require_society_member, require_society_admin
from app.authentication.models import UserModel
from app.complaints.schemas import (
    ComplaintCreate,
    ComplaintAssignRequest,
    ComplaintStatusUpdateRequest,
    ComplaintResolveRequest,
    ComplaintCloseRequest,
    ComplaintCommentCreate,
    ComplaintCommentResponse,
    ComplaintTicketResponse,
    ComplaintSummaryMetrics,
)
from app.complaints.services.complaint_service import ComplaintService
from app.complaints.routes.common import safe_transaction

router = APIRouter(tags=["Helpdesk & Complaints"])
logger = structlog.get_logger(__name__)


@router.post(
    "/societies/{society_id}/complaints",
    response_model=ComplaintTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_complaint(
    society_id: uuid.UUID,
    payload: ComplaintCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_member),
):
    """
    Resident Endpoint: Report a maintenance issue (personal unit or common area).
    Automatically calculates SLA deadline based on priority (P1: 4h, P2: 24h, P3: 48h, P4: 72h).
    """
    service = ComplaintService(db)
    async with safe_transaction(db):
        ticket = await service.create_complaint(
            user_id=current_user.user_id,
            society_id=society_id,
            payload=payload,
        )
    return await service.get_complaint(society_id, ticket.id)


@router.get(
    "/societies/{society_id}/complaints/my",
    response_model=List[ComplaintTicketResponse],
)
async def list_my_complaints(
    society_id: uuid.UUID,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_member),
):
    """
    Resident Endpoint: List all complaints raised by the logged-in resident.
    """
    service = ComplaintService(db)
    return await service.list_user_complaints(
        society_id=society_id, user_id=current_user.user_id, status_filter=status
    )


@router.get(
    "/societies/{society_id}/complaints/summary",
    response_model=ComplaintSummaryMetrics,
)
async def get_helpdesk_summary(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Admin Endpoint: Helpdesk analytics metrics (total, open, in-progress, resolved, SLA breaches, ratings).
    """
    service = ComplaintService(db)
    return await service.get_summary_metrics(society_id)


@router.get(
    "/societies/{society_id}/complaints",
    response_model=List[ComplaintTicketResponse],
)
async def list_society_complaints(
    society_id: uuid.UUID,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    unit_id: Optional[uuid.UUID] = None,
    assigned_to: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Admin Endpoint: Query society tickets with optional filters.
    """
    service = ComplaintService(db)
    return await service.list_complaints(
        society_id=society_id,
        status_filter=status,
        priority=priority,
        category=category,
        unit_id=unit_id,
        assigned_to_user_id=assigned_to,
    )


@router.get(
    "/societies/{society_id}/complaints/{ticket_id}",
    response_model=ComplaintTicketResponse,
)
async def get_complaint_details(
    society_id: uuid.UUID,
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_member),
):
    """
    Get detailed information for a specific complaint ticket.
    """
    service = ComplaintService(db)
    return await service.get_complaint(society_id=society_id, ticket_id=ticket_id)


@router.post(
    "/societies/{society_id}/complaints/{ticket_id}/assign",
    response_model=ComplaintTicketResponse,
)
async def assign_complaint(
    society_id: uuid.UUID,
    ticket_id: uuid.UUID,
    payload: ComplaintAssignRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Admin Endpoint: Assign a complaint ticket to an internal technician or external vendor.
    """
    service = ComplaintService(db)
    async with safe_transaction(db):
        await service.assign_complaint(
            admin_user_id=current_user.user_id,
            society_id=society_id,
            ticket_id=ticket_id,
            payload=payload,
        )
    return await service.get_complaint(society_id, ticket_id)


@router.patch(
    "/societies/{society_id}/complaints/{ticket_id}/status",
    response_model=ComplaintTicketResponse,
)
async def update_complaint_status(
    society_id: uuid.UUID,
    ticket_id: uuid.UUID,
    payload: ComplaintStatusUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Admin Endpoint: Update ticket status (e.g., in_progress, on_hold).
    """
    service = ComplaintService(db)
    async with safe_transaction(db):
        await service.update_status(
            admin_user_id=current_user.user_id,
            society_id=society_id,
            ticket_id=ticket_id,
            payload=payload,
        )
    return await service.get_complaint(society_id, ticket_id)


@router.post(
    "/societies/{society_id}/complaints/{ticket_id}/resolve",
    response_model=ComplaintTicketResponse,
)
async def resolve_complaint(
    society_id: uuid.UUID,
    ticket_id: uuid.UUID,
    payload: ComplaintResolveRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Admin/Technician Endpoint: Mark complaint as resolved with resolution notes and photos.
    """
    service = ComplaintService(db)
    async with safe_transaction(db):
        await service.resolve_complaint(
            admin_user_id=current_user.user_id,
            society_id=society_id,
            ticket_id=ticket_id,
            payload=payload,
        )
    return await service.get_complaint(society_id, ticket_id)


@router.post(
    "/societies/{society_id}/complaints/{ticket_id}/close",
    response_model=ComplaintTicketResponse,
)
async def close_and_rate_complaint(
    society_id: uuid.UUID,
    ticket_id: uuid.UUID,
    payload: ComplaintCloseRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_member),
):
    """
    Resident Endpoint: Verify resolution, close ticket, and submit 1-5 star satisfaction feedback.
    """
    service = ComplaintService(db)
    async with safe_transaction(db):
        await service.close_complaint(
            resident_user_id=current_user.user_id,
            society_id=society_id,
            ticket_id=ticket_id,
            payload=payload,
        )
    return await service.get_complaint(society_id, ticket_id)


@router.post(
    "/societies/{society_id}/complaints/{ticket_id}/comments",
    response_model=ComplaintCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_complaint_comment(
    society_id: uuid.UUID,
    ticket_id: uuid.UUID,
    payload: ComplaintCommentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_member),
):
    """
    Resident/Admin Endpoint: Post a message or progress update to the ticket activity timeline.
    """
    service = ComplaintService(db)
    async with safe_transaction(db):
        comment = await service.add_comment(
            user_id=current_user.user_id,
            society_id=society_id,
            ticket_id=ticket_id,
            payload=payload,
        )
    return comment


@router.get(
    "/societies/{society_id}/complaints/{ticket_id}/comments",
    response_model=List[ComplaintCommentResponse],
)
async def list_complaint_comments(
    society_id: uuid.UUID,
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_member),
):
    """
    Resident/Admin Endpoint: Retrieve all comments in the ticket activity timeline.
    """
    service = ComplaintService(db)
    # Check if admin to decide whether internal comments should be visible
    is_admin = current_user.role in ("platform_admin", "admin", "society_admin", "committee")
    return await service.list_comments(society_id, ticket_id, include_internal=is_admin)
