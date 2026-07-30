import uuid
import secrets
from typing import Optional, List, Tuple
from datetime import datetime, timedelta, timezone
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.societies.models import SocietyModel, SubscriptionModel, SocietyLeadModel, SubscriptionStatus, UserSocietyRoleModel, SocietyRole
from app.authentication.models import UserModel, AuthCredentialModel, ActivationTokenModel, UserAccountStatus, UserRole, TokenType
from app.core.email_service import EmailService
from app.platform.schemas import (
    RegisterSocietyLeadRequest,
    UpdateSocietyLeadStatusRequest,
    PlatformCreateSocietyRequest,
    PlatformCreateSocietyFromLeadRequest,
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
    async def list_society_leads(cls, db: AsyncSession, status_filter: Optional[str] = None) -> List[SocietyLeadModel]:
        stmt = select(SocietyLeadModel).order_by(SocietyLeadModel.created_at.desc())
        if status_filter:
            stmt = stmt.where(SocietyLeadModel.status == status_filter)
        res = await db.execute(stmt)
        return res.scalars().all()

    @classmethod
    async def get_society_lead_by_id(cls, db: AsyncSession, lead_id: uuid.UUID) -> SocietyLeadModel:
        stmt = select(SocietyLeadModel).where(SocietyLeadModel.id == lead_id)
        res = await db.execute(stmt)
        lead = res.scalar_one_or_none()
        if not lead:
            raise ValueError(f"Society lead with ID '{lead_id}' not found")
        return lead

    @classmethod
    async def update_society_lead_status(cls, db: AsyncSession, lead_id: uuid.UUID, payload: UpdateSocietyLeadStatusRequest) -> SocietyLeadModel:
        lead = await cls.get_society_lead_by_id(db, lead_id)
        lead.status = payload.status
        if payload.comments:
            lead.comments = f"{lead.comments or ''}\n[Update]: {payload.comments}".strip()
        await db.flush()
        logger.info("platform.lead_status_updated", lead_id=str(lead.id), status=payload.status)
        return lead

    @classmethod
    async def create_society(cls, db: AsyncSession, payload: PlatformCreateSocietyRequest) -> SocietyModel:
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
    async def create_society_from_lead(
        cls,
        db: AsyncSession,
        lead_id: uuid.UUID,
        payload: Optional[PlatformCreateSocietyFromLeadRequest] = None
    ) -> Tuple[SocietyModel, SubscriptionModel, dict]:
        """
        One-Click Provisioning Workflow:
        Auto-maps Lead data -> Creates Society -> Creates Subscription -> Provisions Primary Admin -> Sends Resend Activation Email.
        """
        lead = await cls.get_society_lead_by_id(db, lead_id)

        city_prefix = (lead.city[:3] if lead.city else "MUM").upper()
        reg_no = (payload.registration_no if payload and payload.registration_no else f"RWA/{city_prefix}/{datetime.now().year}/{uuid.uuid4().hex[:4].upper()}")
        address = (payload.address if payload and payload.address else f"{lead.city} (Address Verification Pending)")
        state = (payload.state if payload and payload.state else "Maharashtra")
        zipcode = (payload.zipcode if payload and payload.zipcode else "400000")
        plan = (payload.plan if payload and payload.plan else "GOLD")
        valid_months = (payload.valid_months if payload and payload.valid_months else 12)

        # 1. Create Society from Lead Mapping
        soc_req = PlatformCreateSocietyRequest(
            name=lead.organization_name,
            registration_no=reg_no,
            address=address,
            city=lead.city,
            state=state,
            country="India",
            zipcode=zipcode,
            email=lead.email,
            phone=lead.mobile,
        )
        society = await cls.create_society(db, soc_req)

        # 2. Attach Subscription (Uses configured plan or defaults to GOLD)
        expected_admins = lead.expected_admins or 5
        sub_req = PlatformCreateSubscriptionRequest(
            society_id=society.id,
            plan=plan,
            valid_months=valid_months,
            max_admins=max(expected_admins, 5),
            max_storage_gb=20,
        )
        subscription = await cls.create_subscription(db, sub_req)

        # 3. Parse Contact Name
        names = lead.primary_contact_name.strip().split(" ", 1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else "Admin"

        # 4. Provision Admin Account
        admin_req = PlatformCreateAdminRequest(
            society_id=society.id,
            first_name=first_name,
            last_name=last_name,
            email=lead.email,
            mobile=lead.mobile,
        )
        admin_res = await cls.create_primary_admin(db, admin_req)

        # 5. Mark Lead Status as Provisioned
        lead.status = "provisioned"
        await db.flush()

        logger.info("platform.society_auto_provisioned_from_lead", lead_id=str(lead.id), society_id=str(society.id), plan=plan)
        return society, subscription, admin_res

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
        stmt = select(AuthCredentialModel).where(AuthCredentialModel.identifier == payload.email)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ValueError(f"Email '{payload.email}' is already registered in the system")

        stmt_soc = select(SocietyModel).where(SocietyModel.id == payload.society_id)
        res_soc = await db.execute(stmt_soc)
        society = res_soc.scalar_one_or_none()
        if not society:
            raise ValueError(f"Society ID '{payload.society_id}' not found")

        user = UserModel(
            first_name=payload.first_name,
            last_name=payload.last_name,
            role=UserRole.SOCIETY_ADMIN.value,
            status=UserAccountStatus.ACTIVATION_PENDING.value,
            email_verified=True,
        )
        db.add(user)
        await db.flush()

        credential = AuthCredentialModel(
            user_id=user.user_id,
            provider="email",
            identifier=payload.email,
            password_hash=None,
        )
        db.add(credential)

        user_soc_role = UserSocietyRoleModel(
            user_id=user.user_id,
            society_id=payload.society_id,
            role=SocietyRole.SOCIETY_ADMIN.value,
            status="approved",
        )
        db.add(user_soc_role)

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
