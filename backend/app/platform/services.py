import uuid
import secrets
from datetime import datetime, timedelta, timezone
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.societies.models import SocietyModel, SubscriptionModel, SocietyLeadModel, SubscriptionStatus, UserSocietyRoleModel, SocietyRole
from app.authentication.models import UserModel, AuthCredentialModel, ActivationTokenModel, UserAccountStatus, UserRole, TokenType
from app.core.email_service import EmailService
from app.platform.schemas import (
    RegisterSocietyLeadRequest,
    PlatformCreateSocietyRequest,
    PlatformCreateSubscriptionRequest,
    PlatformCreateAdminRequest,
)

logger = structlog.get_logger(__name__)

class PlatformAdminService:

    @classmethod
    async def register_society_lead(cls, db: AsyncSession, payload: RegisterSocietyLeadRequest) -> SocietyLeadModel:
        lead = SocietyLeadModel(
            organization_name=payload.organization_name,
            primary_contact_name=payload.primary_contact_name,
            email=payload.email,
            mobile=payload.mobile,
            city=payload.city,
            expected_flats=payload.expected_flats,
            expected_admins=payload.expected_admins,
            comments=payload.comments,
        )
        db.add(lead)
        await db.flush()

        logger.info("platform.lead_created", lead_id=str(lead.id), org=payload.organization_name)

        # Trigger Resend confirmation email
        EmailService.send_society_lead_confirmation(
            to_email=payload.email,
            contact_name=payload.primary_contact_name,
            org_name=payload.organization_name,
        )

        return lead

    @classmethod
    async def create_society(cls, db: AsyncSession, payload: PlatformCreateSocietyRequest) -> SocietyModel:
        # Check uniqueness of registration_no
        stmt = select(SocietyModel).where(SocietyModel.registration_no == payload.registration_no)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ValueError(f"Society with registration number '{payload.registration_no}' already exists")

        society = SocietyModel(
            name=payload.name,
            registration_no=payload.registration_no,
            address=payload.address,
            city=payload.city,
            state=payload.state,
            country=payload.country,
            zipcode=payload.zipcode,
            email=payload.email,
            phone=payload.phone,
        )
        db.add(society)
        await db.flush()
        logger.info("platform.society_created", society_id=str(society.id), name=society.name)
        return society

    @classmethod
    async def create_subscription(cls, db: AsyncSession, payload: PlatformCreateSubscriptionRequest) -> SubscriptionModel:
        stmt = select(SubscriptionModel).where(SubscriptionModel.society_id == payload.society_id)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise ValueError("Society already has an active or existing subscription")

        now = datetime.now(timezone.utc)
        expiry = now + timedelta(days=payload.valid_months * 30)

        subscription = SubscriptionModel(
            society_id=payload.society_id,
            plan=payload.plan,
            status=SubscriptionStatus.ACTIVE.value,
            start_date=now,
            expiry_date=expiry,
            max_admins=payload.max_admins,
            max_storage_gb=payload.max_storage_gb,
        )
        db.add(subscription)
        await db.flush()
        logger.info("platform.subscription_created", society_id=str(payload.society_id), plan=payload.plan)
        return subscription

    @classmethod
    async def create_primary_admin(cls, db: AsyncSession, payload: PlatformCreateAdminRequest) -> dict:
        # Check if email is already in use
        stmt = select(AuthCredentialModel).where(AuthCredentialModel.identifier == payload.email)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ValueError(f"Email '{payload.email}' is already registered in the system")

        # Verify society exists
        stmt_soc = select(SocietyModel).where(SocietyModel.id == payload.society_id)
        res_soc = await db.execute(stmt_soc)
        society = res_soc.scalar_one_or_none()
        if not society:
            raise ValueError(f"Society ID '{payload.society_id}' not found")

        # Create Admin User in ACTIVATION_PENDING status
        user = UserModel(
            first_name=payload.first_name,
            last_name=payload.last_name,
            role=UserRole.SOCIETY_ADMIN.value,
            status=UserAccountStatus.ACTIVATION_PENDING.value,
            email_verified=True,  # Pre-verified by Platform Admin
        )
        db.add(user)
        await db.flush()

        # Add auth credential (password will be set during activation)
        credential = AuthCredentialModel(
            user_id=user.user_id,
            provider="email",
            identifier=payload.email,
            password_hash=None,
        )
        db.add(credential)

        # Link user role to society
        user_soc_role = UserSocietyRoleModel(
            user_id=user.user_id,
            society_id=payload.society_id,
            role=SocietyRole.SOCIETY_ADMIN.value,
            status="approved",
        )
        db.add(user_soc_role)

        # Generate activation token (valid for 48 hours)
        raw_token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(hours=48)
        activation_token = ActivationTokenModel(
            user_id=user.user_id,
            token=raw_token,
            type=TokenType.ADMIN_ACTIVATION.value,
            expires_at=expiry,
        )
        db.add(activation_token)
        await db.flush()

        # Send activation email via Resend Service
        EmailService.send_admin_activation_email(
            to_email=payload.email,
            name=f"{payload.first_name} {payload.last_name}",
            society_name=society.name,
            token=raw_token,
        )

        logger.info("platform.admin_created", user_id=str(user.user_id), email=payload.email, society=society.name)

        return {
            "user_id": str(user.user_id),
            "email": payload.email,
            "society_id": str(payload.society_id),
            "activation_token": raw_token,
            "status": "activation_email_sent",
        }
