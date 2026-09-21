import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from app.notices.models import (
    NoticeModel,
    NoticeReadReceiptModel,
    NoticeCategory,
    NoticeTargetAudience,
    NoticePriority,
)
from app.notices.repository import NoticeRepository
from app.notices.services.notice_service import NoticeService
from app.notices.schemas import (
    NoticeCreate,
    NoticeUpdate,
)
from app.societies.models import SocietyModel, BuildingModel, FloorModel, UnitModel, UserSocietyRoleModel
from app.authentication.models import UserModel


@pytest.fixture
async def notice_test_data(db_session):
    society = SocietyModel(
        id=uuid.uuid4(),
        name="Maple Leaf Society",
        registration_no=f"REG-{uuid.uuid4().hex[:6]}",
        address="102 Lake View",
        city="Mumbai",
        state="Maharashtra",
        country="India",
        zipcode="400050",
    )
    db_session.add(society)
    await db_session.flush()

    building = BuildingModel(id=uuid.uuid4(), society_id=society.id, name="Wing A")
    db_session.add(building)
    await db_session.flush()

    floor = FloorModel(id=uuid.uuid4(), building_id=building.id, floor_number=1)
    db_session.add(floor)
    await db_session.flush()

    unit = UnitModel(
        id=uuid.uuid4(),
        floor_id=floor.id,
        unit_number="101",
        unit_type="flat",
        status="occupied",
    )
    db_session.add(unit)
    await db_session.flush()

    admin = UserModel(
        user_id=uuid.uuid4(),
        first_name="Secretary",
        last_name="RWA",
        role="society_admin",
        status="active",
        email_verified=True,
    )
    db_session.add(admin)

    resident = UserModel(
        user_id=uuid.uuid4(),
        first_name="Meera",
        last_name="Nair",
        role="resident",
        status="active",
        email_verified=True,
    )
    db_session.add(resident)
    await db_session.flush()

    # Link resident to unit in society
    member_role = UserSocietyRoleModel(
        id=uuid.uuid4(),
        user_id=resident.user_id,
        society_id=society.id,
        unit_id=unit.id,
        role="resident",
        status="approved",
    )
    db_session.add(member_role)
    await db_session.commit()

    return {
        "society": society,
        "building": building,
        "floor": floor,
        "unit": unit,
        "admin": admin,
        "resident": resident,
    }


# ============================================================================
# Notice Repository Tests
# ============================================================================

@pytest.mark.asyncio
async def test_notice_repository_lifecycle_and_reads(db_session, notice_test_data):
    repo = NoticeRepository(db_session)
    data = notice_test_data

    # 1. Create pinned notice
    n1 = NoticeModel(
        society_id=data["society"].id,
        created_by_user_id=data["admin"].user_id,
        title="Emergency Water Shutdown",
        content="Water supply will be paused tomorrow from 2 PM to 5 PM for pipe replacement.",
        category=NoticeCategory.EMERGENCY.value,
        priority=NoticePriority.URGENT.value,
        target_audience=NoticeTargetAudience.ALL.value,
        is_pinned=True,
    )
    saved1 = await repo.create_notice(n1)
    assert saved1.id is not None
    assert saved1.is_pinned is True

    # 2. Record read receipt
    receipt = await repo.record_read_receipt(saved1.id, data["resident"].user_id)
    assert receipt.id is not None
    assert receipt.user_id == data["resident"].user_id

    # Duplicate read receipt is idempotent
    receipt2 = await repo.record_read_receipt(saved1.id, data["resident"].user_id)
    assert receipt2.id == receipt.id

    # Read count
    read_count = await repo.get_read_count(saved1.id)
    assert read_count == 1

    # Check is_read_by_user
    is_read = await repo.is_read_by_user(saved1.id, data["resident"].user_id)
    assert is_read is True


# ============================================================================
# Notice Service Tests
# ============================================================================

@pytest.mark.asyncio
async def test_notice_service_publishing_and_audience(db_session, notice_test_data):
    service = NoticeService(db_session)
    data = notice_test_data

    # 1. Publish society-wide notice
    payload = NoticeCreate(
        title="Diwali Celebration 2026",
        content="Join us for Diwali festivities at the central lawn this Saturday.",
        category="festival",
        priority="normal",
        target_audience="all",
        is_pinned=False,
    )
    notice = await service.publish_notice(
        user_id=data["admin"].user_id,
        society_id=data["society"].id,
        payload=payload,
    )
    assert notice.id is not None
    assert notice.title == "Diwali Celebration 2026"

    # 2. Publish building-specific notice for Wing A
    building_notice = await service.publish_notice(
        user_id=data["admin"].user_id,
        society_id=data["society"].id,
        payload=NoticeCreate(
            title="Wing A Elevator Servicing",
            content="Lift A1 will be under maintenance on Thursday.",
            category="maintenance",
            target_audience="building",
            target_building_id=data["building"].id,
            is_pinned=True,
        ),
    )
    assert building_notice.id is not None

    # 3. Resident lists active notices (both should appear because resident is in Wing A)
    resident_notices = await service.list_active_notices_for_user(
        society_id=data["society"].id, user_id=data["resident"].user_id
    )
    assert len(resident_notices) == 2
    # Pinned building notice should appear first
    assert resident_notices[0]["is_pinned"] is True
    assert resident_notices[0]["title"] == "Wing A Elevator Servicing"

    # 4. Fetch notice details (should auto-record read receipt)
    details = await service.get_notice(
        society_id=data["society"].id,
        notice_id=notice.id,
        current_user_id=data["resident"].user_id,
    )
    assert details["is_read_by_me"] is True
    assert details["read_count"] == 1

    # 5. Check stats
    stats = await service.get_notice_stats(data["society"].id, notice.id)
    assert stats["total_reads"] == 1

    # 6. Update notice
    updated = await service.update_notice(
        admin_user_id=data["admin"].user_id,
        society_id=data["society"].id,
        notice_id=notice.id,
        payload=NoticeUpdate(is_pinned=True),
    )
    assert updated.is_pinned is True

    # 7. Delete notice
    await service.delete_notice(
        admin_user_id=data["admin"].user_id,
        society_id=data["society"].id,
        notice_id=notice.id,
    )
    with pytest.raises(HTTPException) as exc:
        await service.get_notice(data["society"].id, notice.id)
    assert exc.value.status_code == 404
