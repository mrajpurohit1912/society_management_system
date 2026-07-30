import uuid
from typing import Optional
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.database import get_db_session
from app.platform.schemas import (
    RegisterSocietyLeadRequest,
    UpdateSocietyLeadStatusRequest,
    PlatformCreateSocietyRequest,
    PlatformCreateSocietyFromLeadRequest,
    PlatformCreateSubscriptionRequest,
    PlatformCreateAdminRequest,
)
from app.platform.services import PlatformAdminService
from app.societies.models import SocietyModel, SubscriptionModel, SocietyLeadModel
from app.authentication.models import UserModel

router = APIRouter(tags=["Platform & Lead Management"])
logger = structlog.get_logger(__name__)

@router.post("/register-society", status_code=status.HTTP_201_CREATED)
async def register_society_lead(
    payload: RegisterSocietyLeadRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Public Endpoint: Allows prospective society representatives to register interest.
    Saves the lead and sends an automated confirmation email via Resend.
    """
    try:
        async with db.begin():
            lead = await PlatformAdminService.register_society_lead(db, payload)
        return {
            "success": True,
            "message": "Society registration interest received. Our team will contact you shortly.",
            "data": {
                "lead_id": str(lead.id),
                "organization_name": lead.organization_name,
                "status": lead.status,
            }
        }
    except Exception as e:
        logger.exception("platform.register_lead_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/platform/leads")
async def list_platform_leads(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Platform Admin Endpoint: List all incoming society registration inquiries.
    """
    leads = await PlatformAdminService.list_society_leads(db, status_filter=status)
    return {
        "success": True,
        "count": len(leads),
        "data": [
            {
                "lead_id": str(lead.id),
                "organization_name": lead.organization_name,
                "primary_contact_name": lead.primary_contact_name,
                "email": lead.email,
                "mobile": lead.mobile,
                "city": lead.city,
                "expected_flats": lead.expected_flats,
                "expected_admins": lead.expected_admins,
                "comments": lead.comments,
                "status": lead.status,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
            }
            for lead in leads
        ]
    }


@router.get("/platform/leads/{lead_id}")
async def get_platform_lead_details(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Platform Admin Endpoint: Get full details of a specific society registration lead.
    """
    try:
        lead = await PlatformAdminService.get_society_lead_by_id(db, lead_id)
        return {
            "success": True,
            "data": {
                "lead_id": str(lead.id),
                "organization_name": lead.organization_name,
                "primary_contact_name": lead.primary_contact_name,
                "email": lead.email,
                "mobile": lead.mobile,
                "city": lead.city,
                "expected_flats": lead.expected_flats,
                "expected_admins": lead.expected_admins,
                "comments": lead.comments,
                "status": lead.status,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/platform/leads/{lead_id}")
async def update_platform_lead_status(
    lead_id: uuid.UUID,
    payload: UpdateSocietyLeadStatusRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Platform Admin Endpoint: Update lead status (e.g. lead_created, in_discussion, provisioned, rejected).
    """
    try:
        async with db.begin():
            lead = await PlatformAdminService.update_society_lead_status(db, lead_id, payload)
        return {
            "success": True,
            "message": "Lead status updated successfully",
            "data": {
                "lead_id": str(lead.id),
                "organization_name": lead.organization_name,
                "status": lead.status,
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/platform/societies", status_code=status.HTTP_201_CREATED)
async def platform_create_society(
    payload: PlatformCreateSocietyRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Platform Admin Endpoint: Provision a new Society in the platform manually.
    """
    try:
        async with db.begin():
            society = await PlatformAdminService.create_society(db, payload)
        return {
            "success": True,
            "message": "Society created successfully",
            "data": {
                "society_id": str(society.id),
                "name": society.name,
                "registration_no": society.registration_no,
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/platform/societies/from-lead/{lead_id}", status_code=status.HTTP_201_CREATED)
async def platform_create_society_from_lead(
    lead_id: uuid.UUID,
    payload: Optional[PlatformCreateSocietyFromLeadRequest] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Platform Admin Endpoint: ONE-CLICK Auto-Provisioning Workflow from Lead!
    Maps Lead -> Creates Society -> Creates Subscription -> Provisions Primary Admin -> Sends Resend Activation Email.
    """
    try:
        async with db.begin():
            society, subscription, admin_res = await PlatformAdminService.create_society_from_lead(db, lead_id, payload)
        return {
            "success": True,
            "message": "Society, Subscription, and Primary Admin successfully provisioned from Lead! Activation email dispatched via Resend.",
            "data": {
                "society_id": str(society.id),
                "society_name": society.name,
                "registration_no": society.registration_no,
                "subscription_id": str(subscription.id),
                "plan": subscription.plan,
                "admin_user_id": admin_res["user_id"],
                "admin_email": admin_res["email"],
                "activation_token": admin_res["activation_token"],
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/platform/subscriptions", status_code=status.HTTP_201_CREATED)
async def platform_create_subscription(
    payload: PlatformCreateSubscriptionRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Platform Admin Endpoint: Attach/Enable an offline paid Subscription for a Society.
    """
    try:
        async with db.begin():
            subscription = await PlatformAdminService.create_subscription(db, payload)
        return {
            "success": True,
            "message": "Subscription activated successfully",
            "data": {
                "subscription_id": str(subscription.id),
                "society_id": str(subscription.society_id),
                "plan": subscription.plan,
                "status": subscription.status,
                "expiry_date": subscription.expiry_date.isoformat(),
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/platform/admins", status_code=status.HTTP_201_CREATED)
async def platform_create_admin(
    payload: PlatformCreateAdminRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Platform Admin Endpoint: Provision a Primary Society Admin.
    Generates an activation token and sends a set-password activation email via Resend.
    """
    try:
        async with db.begin():
            res = await PlatformAdminService.create_primary_admin(db, payload)
        return {
            "success": True,
            "message": "Primary Society Admin provisioned. Activation email sent via Resend.",
            "data": res
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/platform/dashboard")
async def platform_dashboard(
    db: AsyncSession = Depends(get_db_session),
):
    """
    Platform Admin Endpoint: View high-level metrics (total societies, active subscriptions, leads).
    """
    soc_count = await db.scalar(select(func.count(SocietyModel.id)))
    sub_count = await db.scalar(select(func.count(SubscriptionModel.id)).where(SubscriptionModel.status == "active"))
    user_count = await db.scalar(select(func.count(UserModel.user_id)))
    lead_count = await db.scalar(select(func.count(SocietyLeadModel.id)))

    return {
        "success": True,
        "data": {
            "total_societies": soc_count or 0,
            "active_subscriptions": sub_count or 0,
            "total_users": user_count or 0,
            "total_leads": lead_count or 0,
        }
    }
