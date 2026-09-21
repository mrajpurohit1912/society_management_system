import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from app.visitors.models import (
    VisitorPassModel,
    VisitorLogModel,
    VisitorType,
    VisitorPassStatus,
    VisitorLogStatus,
    EntryType,
)
from app.visitors.repository import VisitorRepository
from app.visitors.services.pass_service import PassService
from app.visitors.services.gatekeeper_service import GatekeeperService
from app.visitors.schemas import (
    VisitorPassCreate,
    PasscodeCheckInRequest,
    QRCheckInRequest,
    QuickCheckInRequest,
    CheckOutRequest,
)
from app.societies.models import SocietyModel, BuildingModel, FloorModel, UnitModel
from app.authentication.models import UserModel


@pytest.fixture
async def visitor_test_data(db_session):
    """
    Sets up basic hierarchy: Society, Building, Floor, Unit, Resident User, and Guard User.
    """
    society = SocietyModel(
        id=uuid.uuid4(),
        name="Silver Oak Society",
        registration_no=f"REG-{uuid.uuid4().hex[:6]}",
        address="101 Tech Boulevard",
        city="Bengaluru",
        state="Karnataka",
        country="India",
        zipcode="560100",
    )
    db_session.add(society)
    await db_session.flush()

    building = BuildingModel(id=uuid.uuid4(), society_id=society.id, name="Wing B")
    db_session.add(building)
    await db_session.flush()

    floor = FloorModel(id=uuid.uuid4(), building_id=building.id, floor_number=3)
    db_session.add(floor)
    await db_session.flush()

    unit = UnitModel(
        id=uuid.uuid4(),
        floor_id=floor.id,
        unit_number="B-304",
        unit_type="flat",
        status="occupied",
    )
    db_session.add(unit)
    await db_session.flush()

    resident = UserModel(
        user_id=uuid.uuid4(),
        first_name="Rohan",
        last_name="Verma",
        role="resident",
        status="active",
        email_verified=True,
    )
    db_session.add(resident)

    guard = UserModel(
        user_id=uuid.uuid4(),
        first_name="Security",
        last_name="Guard",
        role="security_guard",
        status="active",
        email_verified=True,
    )
    db_session.add(guard)
    await db_session.commit()

    return {
        "society": society,
        "building": building,
        "floor": floor,
        "unit": unit,
        "resident": resident,
        "guard": guard,
    }


# ============================================================================
# Visitor Repository Tests
# ============================================================================

@pytest.mark.asyncio
async def test_repository_pass_lifecycle(db_session, visitor_test_data):
    repo = VisitorRepository(db_session)
    data = visitor_test_data

    pass_record = VisitorPassModel(
        society_id=data["society"].id,
        unit_id=data["unit"].id,
        created_by_user_id=data["resident"].user_id,
        visitor_name="Vikram Seth",
        visitor_phone="+919876543210",
        visitor_type=VisitorType.GUEST.value,
        passcode="123456",
        qr_code_token="token_qr_abc12345",
        valid_from=datetime.now(timezone.utc) - timedelta(hours=1),
        valid_until=datetime.now(timezone.utc) + timedelta(hours=10),
        status=VisitorPassStatus.ACTIVE.value,
    )
    saved_pass = await repo.create_pass(pass_record)
    assert saved_pass.id is not None
    assert saved_pass.visitor_name == "Vikram Seth"

    # Get by ID
    fetched = await repo.get_pass_by_id(saved_pass.id)
    assert fetched is not None
    assert fetched.passcode == "123456"

    # Get valid by passcode
    by_code = await repo.get_valid_pass_by_code(data["society"].id, "123456")
    assert by_code is not None
    assert by_code.id == saved_pass.id

    # Get valid by QR
    by_qr = await repo.get_valid_pass_by_qr(data["society"].id, "token_qr_abc12345")
    assert by_qr is not None
    assert by_qr.id == saved_pass.id

    # List by user
    user_passes = await repo.list_passes_by_user(data["resident"].user_id)
    assert len(user_passes) == 1

    # List by unit
    unit_passes = await repo.list_passes_by_unit(data["unit"].id)
    assert len(unit_passes) == 1

    # Update pass
    saved_pass.status = VisitorPassStatus.REVOKED.value
    updated = await repo.update_pass(saved_pass)
    assert updated.status == VisitorPassStatus.REVOKED.value

    # After revoking, get_valid_pass_by_code should return None
    invalid_code = await repo.get_valid_pass_by_code(data["society"].id, "123456")
    assert invalid_code is None


@pytest.mark.asyncio
async def test_repository_log_lifecycle_and_summary(db_session, visitor_test_data):
    repo = VisitorRepository(db_session)
    data = visitor_test_data

    # Create quick check-in log
    log1 = VisitorLogModel(
        society_id=data["society"].id,
        unit_id=data["unit"].id,
        pass_id=None,
        visitor_name="Swiggy Delivery Boy",
        visitor_phone="+919999988888",
        visitor_type=VisitorType.DELIVERY.value,
        entry_type=EntryType.QUICK_CHECKIN.value,
        status=VisitorLogStatus.INSIDE.value,
        company_name="Swiggy",
        gate_number="Gate 1",
        checked_in_by=data["guard"].user_id,
        check_in_time=datetime.now(timezone.utc) - timedelta(hours=5),  # Overstay > 4h
    )
    saved_log1 = await repo.create_log(log1)
    assert saved_log1.id is not None

    # Create active guest log
    log2 = VisitorLogModel(
        society_id=data["society"].id,
        unit_id=data["unit"].id,
        pass_id=None,
        visitor_name="Uber Driver",
        visitor_phone="+919999977777",
        visitor_type=VisitorType.CAB.value,
        entry_type=EntryType.QUICK_CHECKIN.value,
        status=VisitorLogStatus.INSIDE.value,
        company_name="Uber",
        gate_number="Gate 2",
        checked_in_by=data["guard"].user_id,
        check_in_time=datetime.now(timezone.utc) - timedelta(minutes=30),
    )
    await repo.create_log(log2)

    # Active visitors
    active = await repo.list_active_visitors_by_society(data["society"].id)
    assert len(active) == 2

    # Query logs with filter
    delivery_logs = await repo.list_logs_by_society(
        data["society"].id, visitor_type=VisitorType.DELIVERY.value
    )
    assert len(delivery_logs) == 1

    # Check summary
    summary = await repo.get_active_visitors_summary(data["society"].id)
    assert summary["total_inside"] == 2
    assert summary["deliveries_inside"] == 1
    assert summary["cabs_inside"] == 1
    assert summary["overstay_count"] == 1  # log1 check_in_time > 4h ago

    # Checkout log1
    saved_log1.status = VisitorLogStatus.CHECKED_OUT.value
    saved_log1.check_out_time = datetime.now(timezone.utc)
    saved_log1.checked_out_by = data["guard"].user_id
    await repo.update_log(saved_log1)

    # Summary after checkout
    summary_after = await repo.get_active_visitors_summary(data["society"].id)
    assert summary_after["total_inside"] == 1
    assert summary_after["deliveries_inside"] == 0


# ============================================================================
# PassService Tests
# ============================================================================

@pytest.mark.asyncio
async def test_pass_service_create_and_revoke(db_session, visitor_test_data):
    service = PassService(db_session)
    data = visitor_test_data

    payload = VisitorPassCreate(
        unit_id=data["unit"].id,
        visitor_name="Anita Roy",
        visitor_phone="+919876500000",
        visitor_type="guest",
        valid_hours=24,
        vehicle_number="KA01AB1111",
        notes="Dinner guest",
    )

    created_pass = await service.create_visitor_pass(
        user_id=data["resident"].user_id,
        society_id=data["society"].id,
        data=payload,
    )
    assert created_pass.id is not None
    assert len(created_pass.passcode) == 6
    assert created_pass.passcode.isdigit()
    assert created_pass.status == VisitorPassStatus.ACTIVE.value
    assert created_pass.qr_code_token is not None

    # Retrieve pass
    fetched = await service.get_pass(created_pass.id)
    assert fetched.id == created_pass.id

    # Revoke pass by creator
    revoked = await service.revoke_pass(data["resident"].user_id, created_pass.id)
    assert revoked.status == VisitorPassStatus.REVOKED.value

    # Attempting to revoke again raises 400
    with pytest.raises(HTTPException) as exc_info:
        await service.revoke_pass(data["resident"].user_id, created_pass.id)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_pass_service_validation_errors(db_session, visitor_test_data):
    service = PassService(db_session)
    data = visitor_test_data

    # Invalid society
    with pytest.raises(HTTPException) as exc_info:
        await service.create_visitor_pass(
            user_id=data["resident"].user_id,
            society_id=uuid.uuid4(),
            data=VisitorPassCreate(
                unit_id=data["unit"].id,
                visitor_name="Ghost",
                visitor_phone="+919876543210",
            ),
        )
    assert exc_info.value.status_code == 404
    assert "Society not found" in exc_info.value.detail

    # Invalid unit
    with pytest.raises(HTTPException) as exc_info:
        await service.create_visitor_pass(
            user_id=data["resident"].user_id,
            society_id=data["society"].id,
            data=VisitorPassCreate(
                unit_id=uuid.uuid4(),
                visitor_name="Ghost",
                visitor_phone="+919876543210",
            ),
        )
    assert exc_info.value.status_code == 404
    assert "Unit not found" in exc_info.value.detail


# ============================================================================
# GatekeeperService Tests
# ============================================================================

@pytest.mark.asyncio
async def test_gatekeeper_passcode_and_qr_checkin(db_session, visitor_test_data):
    pass_service = PassService(db_session)
    gate_service = GatekeeperService(db_session)
    data = visitor_test_data

    # Create active pass
    pass_record = await pass_service.create_visitor_pass(
        user_id=data["resident"].user_id,
        society_id=data["society"].id,
        data=VisitorPassCreate(
            unit_id=data["unit"].id,
            visitor_name="Pooja Hegde",
            visitor_phone="+919876543299",
            visitor_type="guest",
        ),
    )

    # 1. Gatekeeper checks in with passcode
    checkin_payload = PasscodeCheckInRequest(
        passcode=pass_record.passcode,
        gate_number="Gate 1 - Main",
    )
    log_entry = await gate_service.verify_and_checkin_passcode(
        guard_id=data["guard"].user_id,
        society_id=data["society"].id,
        payload=checkin_payload,
    )
    assert log_entry.id is not None
    assert log_entry.status == VisitorLogStatus.INSIDE.value
    assert log_entry.visitor_name == "Pooja Hegde"

    # Pass should now be COMPLETED
    reloaded_pass = await pass_service.get_pass(pass_record.id)
    assert reloaded_pass.status == VisitorPassStatus.COMPLETED.value

    # Re-checkin with same completed pass should fail (not found / expired)
    with pytest.raises(HTTPException) as exc_info:
        await gate_service.verify_and_checkin_passcode(
            guard_id=data["guard"].user_id,
            society_id=data["society"].id,
            payload=checkin_payload,
        )
    assert exc_info.value.status_code == 404

    # 2. Test QR checkin with new pass
    pass_record_qr = await pass_service.create_visitor_pass(
        user_id=data["resident"].user_id,
        society_id=data["society"].id,
        data=VisitorPassCreate(
            unit_id=data["unit"].id,
            visitor_name="Sanjay Gupta",
            visitor_phone="+919876543288",
            visitor_type="guest",
        ),
    )
    qr_payload = QRCheckInRequest(
        qr_token=pass_record_qr.qr_code_token,
        gate_number="Gate 2 - VIP",
    )
    qr_log = await gate_service.verify_and_checkin_qr(
        guard_id=data["guard"].user_id,
        society_id=data["society"].id,
        payload=qr_payload,
    )
    assert qr_log.status == VisitorLogStatus.INSIDE.value
    assert qr_log.visitor_name == "Sanjay Gupta"

    # Checkout QR visitor
    checkout_res = await gate_service.checkout_visitor(
        guard_id=data["guard"].user_id,
        society_id=data["society"].id,
        log_id=qr_log.id,
        payload=CheckOutRequest(gate_number="Gate 2 - VIP"),
    )
    assert checkout_res.status == VisitorLogStatus.CHECKED_OUT.value
    assert checkout_res.check_out_time is not None


@pytest.mark.asyncio
async def test_gatekeeper_quick_checkin(db_session, visitor_test_data):
    gate_service = GatekeeperService(db_session)
    data = visitor_test_data

    quick_payload = QuickCheckInRequest(
        unit_id=data["unit"].id,
        visitor_name="Zomato Courier",
        visitor_phone="+919123456789",
        visitor_type="delivery",
        company_name="Zomato",
        vehicle_number="KA04EZ9999",
        gate_number="Gate 3",
    )

    log_entry = await gate_service.quick_checkin(
        guard_id=data["guard"].user_id,
        society_id=data["society"].id,
        payload=quick_payload,
    )
    assert log_entry.id is not None
    assert log_entry.entry_type == EntryType.QUICK_CHECKIN.value
    assert log_entry.company_name == "Zomato"
    assert log_entry.status == VisitorLogStatus.INSIDE.value

    # Quick checkin with nonexistent unit raises 404
    with pytest.raises(HTTPException) as exc_info:
        await gate_service.quick_checkin(
            guard_id=data["guard"].user_id,
            society_id=data["society"].id,
            payload=QuickCheckInRequest(
                unit_id=uuid.uuid4(),
                visitor_name="Driver",
                visitor_phone="+919000000000",
            ),
        )
    assert exc_info.value.status_code == 404
