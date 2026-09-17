import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.platform.repository import PlatformRepository
from app.platform.services import PlatformAdminService
from app.platform.schemas import (
    RegisterSocietyLeadRequest,
    UpdateSocietyLeadStatusRequest,
    PlatformCreateSocietyRequest,
    PlatformCreateSocietyFromLeadRequest,
    PlatformCreateSubscriptionRequest,
    PlatformCreateAdminRequest,
)
from app.societies.models import SocietyLeadModel, SocietyModel, SubscriptionModel
from app.authentication.models import UserModel, AuthCredentialModel


@pytest.mark.asyncio
async def test_platform_repository_create_and_get_lead(db_session):
    repo = PlatformRepository(db_session)
    lead = SocietyLeadModel(
        organization_name="Silver Oaks",
        primary_contact_name="Rajesh Kumar",
        email="rajesh@silveroaks.com",
        mobile="+919876543210",
        city="Pune",
        expected_flats=50,
        expected_admins=2,
        comments="Trial request",
    )
    saved = await repo.create_lead(lead)
    assert saved.id is not None
    assert saved.organization_name == "Silver Oaks"

    fetched = await repo.get_lead_by_id(saved.id)
    assert fetched is not None
    assert fetched.email == "rajesh@silveroaks.com"


@pytest.mark.asyncio
async def test_platform_repository_list_leads_with_filter(db_session):
    repo = PlatformRepository(db_session)
    lead1 = SocietyLeadModel(
        organization_name="Lead 1",
        primary_contact_name="Contact 1",
        email="l1@test.com",
        mobile="111",
        city="Pune",
        status="lead_created",
    )
    lead2 = SocietyLeadModel(
        organization_name="Lead 2",
        primary_contact_name="Contact 2",
        email="l2@test.com",
        mobile="222",
        city="Pune",
        status="contacted",
    )
    await repo.create_lead(lead1)
    await repo.create_lead(lead2)

    all_leads = await repo.list_leads()
    assert len(all_leads) >= 2

    contacted = await repo.list_leads(status_filter="contacted")
    assert all(l.status == "contacted" for l in contacted)


@pytest.mark.asyncio
async def test_platform_repository_subscription(db_session):
    repo = PlatformRepository(db_session)
    society_id = uuid.uuid4()
    # Create society first to satisfy foreign key
    from datetime import datetime, timezone, timedelta
    society = SocietyModel(
        id=society_id,
        name="Rep Society",
        registration_no=f"REG/{uuid.uuid4().hex[:6]}",
        address="Test",
        city="City",
        state="State",
        country="Country",
        zipcode="12345",
    )
    db_session.add(society)
    await db_session.flush()

    sub = SubscriptionModel(
        society_id=society_id,
        plan="PLATINUM",
        status="active",
        start_date=datetime.now(timezone.utc),
        expiry_date=datetime.now(timezone.utc) + timedelta(days=365),
        max_admins=10,
        max_storage_gb=50,
    )
    saved_sub = await repo.create_subscription(sub)
    assert saved_sub.id is not None

    fetched = await repo.get_subscription_by_society_id(society_id)
    assert fetched is not None
    assert fetched.plan == "PLATINUM"


@pytest.mark.asyncio
async def test_platform_repository_dashboard_metrics(db_session):
    repo = PlatformRepository(db_session)
    metrics = await repo.get_dashboard_metrics()
    assert "total_societies" in metrics
    assert "active_subscriptions" in metrics
    assert "total_users" in metrics
    assert "total_leads" in metrics


@pytest.mark.asyncio
async def test_platform_service_register_lead():
    mock_db = AsyncMock()
    mock_platform_repo = AsyncMock()
    mock_platform_repo.create_lead.side_effect = lambda lead: lead

    service = PlatformAdminService(
        db=mock_db,
        platform_repo=mock_platform_repo,
    )

    payload = RegisterSocietyLeadRequest(
        organization_name="Green Palms",
        primary_contact_name="Anita Sharma",
        email="anita@palms.com",
        mobile="+919876543211",
        city="Bengaluru",
    )

    with patch("app.platform.services.EmailService.send_society_lead_confirmation") as mock_email:
        lead = await service.register_lead(payload)
        assert lead.organization_name == "Green Palms"
        mock_platform_repo.create_lead.assert_called_once()
        mock_email.assert_called_once_with(
            to_email="anita@palms.com",
            contact_name="Anita Sharma",
            org_name="Green Palms",
        )


@pytest.mark.asyncio
async def test_platform_service_create_new_society_duplicate():
    mock_db = AsyncMock()
    mock_soc_repo = AsyncMock()
    mock_soc_repo.get_society_by_reg_no.return_value = MagicMock(id=uuid.uuid4())

    service = PlatformAdminService(
        db=mock_db,
        society_repo=mock_soc_repo,
    )

    payload = PlatformCreateSocietyRequest(
        name="Duplicate Society",
        registration_no="REG/DUP/001",
        address="Address",
        city="City",
        state="State",
        country="India",
        zipcode="123456",
    )

    with pytest.raises(ValueError, match="already exists"):
        await service.create_new_society(payload)


@pytest.mark.asyncio
async def test_platform_service_create_new_subscription_duplicate():
    mock_db = AsyncMock()
    mock_platform_repo = AsyncMock()
    mock_platform_repo.get_subscription_by_society_id.return_value = MagicMock(id=uuid.uuid4())

    service = PlatformAdminService(
        db=mock_db,
        platform_repo=mock_platform_repo,
    )

    payload = PlatformCreateSubscriptionRequest(
        society_id=uuid.uuid4(),
        plan="GOLD",
        valid_months=12,
        max_admins=5,
        max_storage_gb=10,
    )

    with pytest.raises(ValueError, match="already has an active or existing subscription"):
        await service.create_new_subscription(payload)


@pytest.mark.asyncio
async def test_platform_service_provision_primary_admin_email_exists():
    mock_db = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_user_repo.get_credential_by_identifier.return_value = MagicMock(id=1)

    service = PlatformAdminService(
        db=mock_db,
        user_repo=mock_user_repo,
    )

    payload = PlatformCreateAdminRequest(
        society_id=uuid.uuid4(),
        first_name="John",
        last_name="Doe",
        email="existing@example.com",
        mobile="+919876543210",
    )

    with pytest.raises(ValueError, match="already registered"):
        await service.provision_primary_admin(payload)
