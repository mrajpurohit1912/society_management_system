import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_society_admin
from app.authentication.models import UserModel
from app.societies.schemas import RequestMembershipPayload, RejectMembershipPayload
from app.societies import routes
from app.societies.routes.common import safe_transaction

router = APIRouter(prefix="/societies")


@router.post("/membership/request", status_code=status.HTTP_201_CREATED)
async def request_membership(
    payload: RequestMembershipPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Resident Endpoint: Submit a membership request to join a specific society and flat unit.
    """
    service = routes.MembershipService(db)
    async with safe_transaction(db):
        res = await service.request_membership(
            user_id=current_user.user_id,
            society_id=payload.society_id,
            unit_id=payload.unit_id,
            role=payload.role or "resident",
        )
        return {
            "success": True,
            "message": "Membership request submitted successfully. Waiting for Society Admin approval.",
            "data": {
                "membership_id": str(res.id),
                "society_id": str(res.society_id),
                "unit_id": str(res.unit_id) if res.unit_id else None,
                "status": res.status,
                "role": res.role,
            },
        }


@router.get("/membership/status")
async def get_membership_status(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Resident Endpoint: Fetch current user's society memberships and statuses.
    """
    service = routes.MembershipService(db)
    memberships = await service.get_user_memberships(current_user.user_id)
    return {
        "success": True,
        "data": [
            {
                "membership_id": str(m.id),
                "society_id": str(m.society_id),
                "unit_id": str(m.unit_id) if m.unit_id else None,
                "role": m.role,
                "status": m.status,
            }
            for m in memberships
        ],
    }


@router.get("/{society_id}/membership/requests")
async def list_pending_membership_requests(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Society Admin Endpoint: List all pending membership requests for the society.
    """
    service = routes.MembershipService(db)
    requests = await service.list_pending_requests(society_id)
    return {
        "success": True,
        "data": [
            {
                "membership_id": str(r.id),
                "user_id": str(r.user_id),
                "society_id": str(r.society_id),
                "unit_id": str(r.unit_id) if r.unit_id else None,
                "role": r.role,
                "status": r.status,
                "requested_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in requests
        ],
    }


@router.post("/{society_id}/membership/{membership_id}/approve")
async def approve_membership_request(
    society_id: uuid.UUID,
    membership_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Society Admin Endpoint: Approve a resident's membership request and trigger automated Resend email.
    """
    service = routes.MembershipService(db)
    async with safe_transaction(db):
        res = await service.approve_membership(membership_id, approved_by_user_id=current_user.user_id)
        return {
            "success": True,
            "message": "Membership request approved successfully! Notification email sent via Resend.",
            "data": {
                "membership_id": str(res.id),
                "user_id": str(res.user_id),
                "status": res.status,
            },
        }


@router.post("/{society_id}/membership/{membership_id}/reject")
async def reject_membership_request(
    society_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: Optional[RejectMembershipPayload] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Society Admin Endpoint: Reject a resident's membership request and trigger automated Resend email.
    """
    reason = payload.reason if payload else None
    service = routes.MembershipService(db)
    async with safe_transaction(db):
        res = await service.reject_membership(membership_id, approved_by_user_id=current_user.user_id, reason=reason)
        return {
            "success": True,
            "message": "Membership request rejected.",
            "data": {
                "membership_id": str(res.id),
                "user_id": str(res.user_id),
                "status": res.status,
            },
        }
