import uuid
import secrets
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta, timezone
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.societies.models import (
    SocietyModel,
    SubscriptionModel,
    SocietyLeadModel,
    SubscriptionStatus,
    SocietyRole,
)
from app.authentication.models import (
    UserModel,
    UserAccountStatus,
    UserRole,
    TokenType,
)
from app.core.email_service import EmailService
from app.platform.schemas import (
    RegisterSocietyLeadRequest,
    UpdateSocietyLeadStatusRequest,
    PlatformCreateSocietyRequest,
    PlatformCreateSocietyFromLeadRequest,
    PlatformCreateSubscriptionRequest,
    PlatformCreateAdminRequest,
)
from app.platform.repository import PlatformRepository
from app.societies.repository import SocietyRepository
from app.authentication.repository import UserRepository

logger = structlog.get_logger(__name__)


class PlatformAdminService:
    """
    Domain Service for Platform Administration and Lead Management.
    Orchestrates business logic across repositories without direct DB access.
    """

    def __init__(
        self,
        db: AsyncSession,
        platform_repo: Optional[PlatformRepository] = None,
        society_repo: Optional[SocietyRepository] = None,
        user_repo: Optional[UserRepository] = None,
    ):
        self.db = db
        self.platform_repo = platform_repo or PlatformRepository(db)
        self.society_repo = society_repo or SocietyRepository(db)
        self.user_repo = user_repo or UserRepository(db)

    # ---------------------------------------------------------
    # Instance Methods
    # ---------------------------------------------------------

    async def register_lead(self, payload: RegisterSocietyLeadRequest) -> SocietyLeadModel:
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
        saved_lead = await self.platform_repo.create_lead(lead)

        logger.info("platform.lead_created", lead_id=str(saved_lead.id), org=payload.organization_name)

        # Trigger Resend confirmation email
        EmailService.send_society_lead_confirmation(
            to_email=payload.email,
            contact_name=payload.primary_contact_name,
            org_name=payload.organization_name,
        )

        return saved_lead

    async def list_leads(self, status_filter: Optional[str] = None) -> List[SocietyLeadModel]:
        return await self.platform_repo.list_leads(status_filter=status_filter)

    async def get_lead(self, lead_id: uuid.UUID) -> SocietyLeadModel:
        lead = await self.platform_repo.get_lead_by_id(lead_id)
        if not lead:
            raise ValueError(f"Society lead with ID '{lead_id}' not found")
        return lead

    async def update_lead_status(
        self, lead_id: uuid.UUID, payload: UpdateSocietyLeadStatusRequest
    ) -> SocietyLeadModel:
        lead = await self.get_lead(lead_id)
        lead.status = payload.status
        if payload.comments:
            lead.comments = f"{lead.comments or ''}\n[Update]: {payload.comments}".strip()
        updated = await self.platform_repo.update_lead(lead)
        logger.info("platform.lead_status_updated", lead_id=str(updated.id), status=payload.status)
        return updated

    async def create_new_society(self, payload: PlatformCreateSocietyRequest) -> SocietyModel:
        existing = await self.society_repo.get_society_by_reg_no(payload.registration_no)
        if existing:
            raise ValueError(f"Society with registration number '{payload.registration_no}' already exists")

        society = await self.society_repo.create_society(payload)
        logger.info("platform.society_created", society_id=str(society.id), name=society.name)
        return society

    async def create_new_subscription(
        self, payload: PlatformCreateSubscriptionRequest
    ) -> SubscriptionModel:
        existing = await self.platform_repo.get_subscription_by_society_id(payload.society_id)
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
        saved_sub = await self.platform_repo.create_subscription(subscription)
        logger.info("platform.subscription_created", society_id=str(payload.society_id), plan=payload.plan)
        return saved_sub

    async def provision_primary_admin(self, payload: PlatformCreateAdminRequest) -> Dict[str, Any]:
        existing_cred = await self.user_repo.get_credential_by_identifier(
            provider="email", identifier=payload.email
        )
        if existing_cred:
            raise ValueError(f"Email '{payload.email}' is already registered in the system")

        society = await self.society_repo.get_society(payload.society_id)
        if not society:
            raise ValueError(f"Society ID '{payload.society_id}' not found")

        # 1. Create Core User
        user = await self.user_repo.create_user(
            first_name=payload.first_name,
            last_name=payload.last_name,
            role=UserRole.SOCIETY_ADMIN.value,
            status=UserAccountStatus.ACTIVATION_PENDING.value,
            email_verified=True,
        )

        # 2. Attach Credential
        await self.user_repo.add_credential(
            user_id=user.user_id,
            provider="email",
            identifier=payload.email,
            password_hash=None,
        )

        # 3. Attach Society Role
        await self.society_repo.create_membership(
            user_id=user.user_id,
            society_id=payload.society_id,
            role=SocietyRole.SOCIETY_ADMIN.value,
            status="approved",
        )

        # 4. Generate Activation Token
        raw_token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(hours=48)
        await self.user_repo.create_activation_token(
            user_id=user.user_id,
            token=raw_token,
            token_type=TokenType.ADMIN_ACTIVATION.value,
            expires_at=expiry,
        )

        # 5. Send Activation Email
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

    async def provision_society_from_lead(
        self,
        lead_id: uuid.UUID,
        payload: Optional[PlatformCreateSocietyFromLeadRequest] = None,
    ) -> Tuple[SocietyModel, SubscriptionModel, Dict[str, Any]]:
        """
        One-Click Provisioning Workflow:
        Auto-maps Lead data -> Creates Society -> Creates Subscription -> Provisions Primary Admin -> Sends Resend Activation Email.
        """
        lead = await self.get_lead(lead_id)

        city_prefix = (lead.city[:3] if lead.city else "MUM").upper()
        reg_no = (
            payload.registration_no
            if payload and payload.registration_no
            else f"RWA/{city_prefix}/{datetime.now().year}/{uuid.uuid4().hex[:4].upper()}"
        )
        address = (
            payload.address
            if payload and payload.address
            else f"{lead.city} (Address Verification Pending)"
        )
        state = payload.state if payload and payload.state else "Maharashtra"
        zipcode = payload.zipcode if payload and payload.zipcode else "400000"
        plan = payload.plan if payload and payload.plan else "GOLD"
        valid_months = payload.valid_months if payload and payload.valid_months else 12

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
        society = await self.create_new_society(soc_req)

        # 2. Attach Subscription
        expected_admins = lead.expected_admins or 5
        sub_req = PlatformCreateSubscriptionRequest(
            society_id=society.id,
            plan=plan,
            valid_months=valid_months,
            max_admins=max(expected_admins, 5),
            max_storage_gb=20,
        )
        subscription = await self.create_new_subscription(sub_req)

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
        admin_res = await self.provision_primary_admin(admin_req)

        # 5. Mark Lead Status as Provisioned
        lead.status = "provisioned"
        await self.platform_repo.update_lead(lead)

        logger.info(
            "platform.society_auto_provisioned_from_lead",
            lead_id=str(lead.id),
            society_id=str(society.id),
            plan=plan,
        )
        return society, subscription, admin_res

    # ---------------------------------------------------------
    # Backward-Compatible Classmethods
    # ---------------------------------------------------------

    @classmethod
    async def register_society_lead(
        cls, db: AsyncSession, payload: RegisterSocietyLeadRequest
    ) -> SocietyLeadModel:
        return await cls(db).register_lead(payload)

    @classmethod
    async def list_society_leads(
        cls, db: AsyncSession, status_filter: Optional[str] = None
    ) -> List[SocietyLeadModel]:
        return await cls(db).list_leads(status_filter=status_filter)

    @classmethod
    async def get_society_lead_by_id(
        cls, db: AsyncSession, lead_id: uuid.UUID
    ) -> SocietyLeadModel:
        return await cls(db).get_lead(lead_id)

    @classmethod
    async def update_society_lead_status(
        cls, db: AsyncSession, lead_id: uuid.UUID, payload: UpdateSocietyLeadStatusRequest
    ) -> SocietyLeadModel:
        return await cls(db).update_lead_status(lead_id, payload)

    @classmethod
    async def create_society(
        cls, db: AsyncSession, payload: PlatformCreateSocietyRequest
    ) -> SocietyModel:
        return await cls(db).create_new_society(payload)

    @classmethod
    async def create_society_from_lead(
        cls,
        db: AsyncSession,
        lead_id: uuid.UUID,
        payload: Optional[PlatformCreateSocietyFromLeadRequest] = None,
    ) -> Tuple[SocietyModel, SubscriptionModel, Dict[str, Any]]:
        return await cls(db).provision_society_from_lead(lead_id, payload)

    @classmethod
    async def create_subscription(
        cls, db: AsyncSession, payload: PlatformCreateSubscriptionRequest
    ) -> SubscriptionModel:
        return await cls(db).create_new_subscription(payload)

    @classmethod
    async def create_primary_admin(
        cls, db: AsyncSession, payload: PlatformCreateAdminRequest
    ) -> Dict[str, Any]:
        return await cls(db).provision_primary_admin(payload)
