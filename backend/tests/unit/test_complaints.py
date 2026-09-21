import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from app.complaints.models import (
    ComplaintTicketModel,
    ComplaintCommentModel,
    ComplaintCategory,
    ComplaintScope,
    ComplaintPriority,
    ComplaintStatus,
)
from app.complaints.repository import ComplaintRepository
from app.complaints.services.complaint_service import ComplaintService
from app.complaints.schemas import (
    ComplaintCreate,
    ComplaintAssignRequest,
    ComplaintStatusUpdateRequest,
    ComplaintResolveRequest,
    ComplaintCloseRequest,
    ComplaintCommentCreate,
)
from app.societies.models import SocietyModel, BuildingModel, FloorModel, UnitModel
from app.authentication.models import UserModel


@pytest.fixture
async def complaint_test_data(db_session):
    """
    Sets up basic hierarchy: Society, Building, Floor, Unit, Resident, Admin, and Technician Staff.
    """
    society = SocietyModel(
        id=uuid.uuid4(),
        name="Oakwood Heights",
        registration_no=f"REG-{uuid.uuid4().hex[:6]}",
        address="789 Ring Road",
        city="Pune",
        state="Maharashtra",
        country="India",
        zipcode="411001",
    )
    db_session.add(society)
    await db_session.flush()

    building = BuildingModel(id=uuid.uuid4(), society_id=society.id, name="Tower 1")
    db_session.add(building)
    await db_session.flush()

    floor = FloorModel(id=uuid.uuid4(), building_id=building.id, floor_number=2)
    db_session.add(floor)
    await db_session.flush()

    unit = UnitModel(
        id=uuid.uuid4(),
        floor_id=floor.id,
        unit_number="102",
        unit_type="flat",
        status="occupied",
    )
    db_session.add(unit)
    await db_session.flush()

    resident = UserModel(
        user_id=uuid.uuid4(),
        first_name="Anil",
        last_name="Kumble",
        role="resident",
        status="active",
        email_verified=True,
    )
    db_session.add(resident)

    admin = UserModel(
        user_id=uuid.uuid4(),
        first_name="RWA",
        last_name="President",
        role="society_admin",
        status="active",
        email_verified=True,
    )
    db_session.add(admin)

    technician = UserModel(
        user_id=uuid.uuid4(),
        first_name="Mohan",
        last_name="Electrician",
        role="committee",
        status="active",
        email_verified=True,
    )
    db_session.add(technician)
    await db_session.commit()

    return {
        "society": society,
        "building": building,
        "floor": floor,
        "unit": unit,
        "resident": resident,
        "admin": admin,
        "technician": technician,
    }


# ============================================================================
# Complaint Repository Tests
# ============================================================================

@pytest.mark.asyncio
async def test_complaint_repository_lifecycle_and_metrics(db_session, complaint_test_data):
    repo = ComplaintRepository(db_session)
    data = complaint_test_data

    # 1. Create ticket
    ticket1 = ComplaintTicketModel(
        society_id=data["society"].id,
        unit_id=data["unit"].id,
        created_by_user_id=data["resident"].user_id,
        ticket_number="TKT-2026-0001",
        title="Water dripping from ceiling",
        description="Water seepage in bedroom ceiling",
        category=ComplaintCategory.PLUMBING.value,
        scope=ComplaintScope.PERSONAL_UNIT.value,
        priority=ComplaintPriority.P1_CRITICAL.value,
        status=ComplaintStatus.OPEN.value,
        sla_deadline=datetime.now(timezone.utc) - timedelta(hours=2),  # Already breached SLA
    )
    saved1 = await repo.create_ticket(ticket1)
    assert saved1.id is not None
    assert saved1.ticket_number == "TKT-2026-0001"

    # 2. Add second ticket
    ticket2 = ComplaintTicketModel(
        society_id=data["society"].id,
        unit_id=None,
        created_by_user_id=data["resident"].user_id,
        ticket_number="TKT-2026-0002",
        title="Lift 2 light not working",
        description="Flickering light in common lift",
        category=ComplaintCategory.ELEVATOR.value,
        scope=ComplaintScope.COMMON_AREA.value,
        priority=ComplaintPriority.P3_MEDIUM.value,
        status=ComplaintStatus.RESOLVED.value,
        sla_deadline=datetime.now(timezone.utc) + timedelta(hours=40),
        resident_rating=5,
    )
    await repo.create_ticket(ticket2)

    # 3. List by society
    society_tickets = await repo.list_tickets_by_society(data["society"].id)
    assert len(society_tickets) == 2

    # 4. List by filter
    plumbing_tickets = await repo.list_tickets_by_society(
        data["society"].id, category=ComplaintCategory.PLUMBING.value
    )
    assert len(plumbing_tickets) == 1
    assert plumbing_tickets[0].id == saved1.id

    # 5. Add comments (public & internal)
    c1 = ComplaintCommentModel(
        ticket_id=saved1.id,
        user_id=data["resident"].user_id,
        comment="Please check urgently",
        is_internal=False,
    )
    await repo.create_comment(c1)

    c2 = ComplaintCommentModel(
        ticket_id=saved1.id,
        user_id=data["admin"].user_id,
        comment="Technician Mohan will inspect at 3 PM",
        is_internal=True,
    )
    await repo.create_comment(c2)

    public_comments = await repo.list_comments(saved1.id, include_internal=False)
    assert len(public_comments) == 1

    all_comments = await repo.list_comments(saved1.id, include_internal=True)
    assert len(all_comments) == 2

    # 6. Check summary metrics
    metrics = await repo.get_summary_metrics(data["society"].id)
    assert metrics["total_tickets"] == 2
    assert metrics["open_tickets"] == 1
    assert metrics["resolved_tickets"] == 1
    assert metrics["overdue_sla_tickets"] == 1  # ticket1 is past SLA
    assert metrics["average_rating"] == 5.0
    assert metrics["by_category"]["plumbing"] == 1
    assert metrics["by_category"]["elevator"] == 1


# ============================================================================
# Complaint Service Tests
# ============================================================================

@pytest.mark.asyncio
async def test_complaint_service_sla_and_lifecycle(db_session, complaint_test_data):
    service = ComplaintService(db_session)
    data = complaint_test_data

    # 1. Create P1 Critical complaint (SLA: 4 hours)
    payload_p1 = ComplaintCreate(
        unit_id=data["unit"].id,
        title="Gas smell near meter",
        description="Strong gas odor near kitchen pipe",
        category="security",
        scope="personal_unit",
        priority="p1_critical",
    )
    ticket_p1 = await service.create_complaint(
        user_id=data["resident"].user_id,
        society_id=data["society"].id,
        payload=payload_p1,
    )
    assert ticket_p1.id is not None
    assert ticket_p1.status == ComplaintStatus.OPEN.value
    assert ticket_p1.ticket_number.startswith("TKT-")

    # Verify SLA deadline is ~4 hours from now
    expected_sla = datetime.now(timezone.utc) + timedelta(hours=4)
    # Check difference within 60 seconds
    assert abs((ticket_p1.sla_deadline.replace(tzinfo=timezone.utc) - expected_sla).total_seconds()) < 60

    # 2. Admin assigns ticket to technician
    assign_payload = ComplaintAssignRequest(
        assigned_to_user_id=data["technician"].user_id,
        assigned_vendor_name="City Gas Emergency Services",
        assigned_vendor_phone="+919111191111",
        notes="Dispatched on priority",
    )
    assigned_ticket = await service.assign_complaint(
        admin_user_id=data["admin"].user_id,
        society_id=data["society"].id,
        ticket_id=ticket_p1.id,
        payload=assign_payload,
    )
    assert assigned_ticket.status == ComplaintStatus.ASSIGNED.value
    assert assigned_ticket.assigned_to_user_id == data["technician"].user_id

    # 3. Update status to in_progress
    in_prog = await service.update_status(
        admin_user_id=data["admin"].user_id,
        society_id=data["society"].id,
        ticket_id=ticket_p1.id,
        payload=ComplaintStatusUpdateRequest(status="in_progress", notes="Technician arrived on site"),
    )
    assert in_prog.status == ComplaintStatus.IN_PROGRESS.value

    # 4. Resolve ticket
    resolve_payload = ComplaintResolveRequest(
        resolution_notes="Tightened safety valve. No leakage detected with sensor.",
        resolution_photos=["https://s3.amazonaws.com/test/fixed.jpg"],
    )
    resolved_ticket = await service.resolve_complaint(
        admin_user_id=data["admin"].user_id,
        society_id=data["society"].id,
        ticket_id=ticket_p1.id,
        payload=resolve_payload,
    )
    assert resolved_ticket.status == ComplaintStatus.RESOLVED.value
    assert resolved_ticket.resolved_at is not None

    # 5. Resident closes ticket with 5-star rating & feedback
    close_payload = ComplaintCloseRequest(
        resident_rating=5,
        resident_feedback="Outstanding response time and professional resolution!",
    )
    closed_ticket = await service.close_complaint(
        resident_user_id=data["resident"].user_id,
        society_id=data["society"].id,
        ticket_id=ticket_p1.id,
        payload=close_payload,
    )
    assert closed_ticket.status == ComplaintStatus.CLOSED.value
    assert closed_ticket.resident_rating == 5
    assert closed_ticket.closed_at is not None


@pytest.mark.asyncio
async def test_complaint_service_validation_rules(db_session, complaint_test_data):
    service = ComplaintService(db_session)
    data = complaint_test_data

    # Ticket creation with invalid society raises 404
    with pytest.raises(HTTPException) as exc:
        await service.create_complaint(
            user_id=data["resident"].user_id,
            society_id=uuid.uuid4(),
            payload=ComplaintCreate(title="Test", description="Test details"),
        )
    assert exc.value.status_code == 404

    # Create normal ticket
    ticket = await service.create_complaint(
        user_id=data["resident"].user_id,
        society_id=data["society"].id,
        payload=ComplaintCreate(title="Tap loose", description="Tap is loose in kitchen"),
    )

    # Closing an un-resolved ticket raises 400
    with pytest.raises(HTTPException) as exc:
        await service.close_complaint(
            resident_user_id=data["resident"].user_id,
            society_id=data["society"].id,
            ticket_id=ticket.id,
            payload=ComplaintCloseRequest(resident_rating=4),
        )
    assert exc.value.status_code == 400
    assert "Ticket must be resolved first" in exc.value.detail

    # Non-creator resident attempting to close raises 403
    other_user_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc:
        await service.close_complaint(
            resident_user_id=other_user_id,
            society_id=data["society"].id,
            ticket_id=ticket.id,
            payload=ComplaintCloseRequest(resident_rating=4),
        )
    assert exc.value.status_code == 403
