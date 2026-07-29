import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.database import get_db_session
from app.platform.schemas import (
    RegisterSocietyLeadRequest,
    PlatformCreateSocietyRequest,
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


@router.post("/platform/societies", status_code=status.HTTP_201_CREATED)
async def platform_create_society(
    payload: PlatformCreateSocietyRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Platform Admin Endpoint: Provision a new Society in the platform.
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
