import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.payments.models import (
    MaintenanceInvoiceModel,
    PaymentModel,
    PaymentReceiptModel,
    InvoiceStatus,
    PaymentStatus,
    PaymentMethod,
)
from app.payments.gateways import (
    MockPaymentGateway,
    ManualOfflineGateway,
    get_payment_gateway,
)
from app.payments.repository import PaymentRepository
from app.payments.services.invoice_service import InvoiceService
from app.payments.services.transaction_service import TransactionService
from app.payments.schemas import (
    InvoiceCreate,
    BulkInvoiceGenerateRequest,
    InitiateOnlinePaymentRequest,
    VerifyOnlinePaymentRequest,
    SubmitOfflinePaymentRequest,
    ReviewOfflinePaymentRequest,
)
from app.societies.models import SocietyModel, BuildingModel, FloorModel, UnitModel
from app.authentication.models import UserModel


# ============================================================================
# Gateway Tests
# ============================================================================

@pytest.mark.asyncio
async def test_mock_payment_gateway():
    gateway = MockPaymentGateway()
    order = await gateway.create_order(amount=5000.0, currency="INR", receipt="RCP-001")
    assert order["status"] == "created"
    assert order["amount"] == 5000.0
    assert order["order_id"].startswith("order_mock_")

    is_valid = await gateway.verify_signature(order["order_id"], "pay_success_123", "dummy_sig")
    assert is_valid is True

    is_invalid = await gateway.verify_signature(order["order_id"], "fail_pay_123", "dummy_sig")
    assert is_invalid is False

    refund = await gateway.process_refund("pay_123", amount=1000.0)
    assert refund["status"] == "processed"
    assert refund["amount"] == 1000.0


def test_manual_offline_gateway_validation():
    assert ManualOfflineGateway.validate_reference("offline_upi_neft", "UTR12345678") is True
    assert ManualOfflineGateway.validate_reference("offline_cheque", "CHQ001") is True
    assert ManualOfflineGateway.validate_reference("offline_cash", "CSH") is False
    assert ManualOfflineGateway.validate_reference("offline_upi_neft", None) is False


def test_get_payment_gateway_factory():
    assert isinstance(get_payment_gateway("online_mock"), MockPaymentGateway)
    assert isinstance(get_payment_gateway("offline_upi_neft"), ManualOfflineGateway)
    assert isinstance(get_payment_gateway("offline_cheque"), ManualOfflineGateway)


# ============================================================================
# Repository Tests
# ============================================================================

@pytest.mark.asyncio
async def test_payment_repository_invoices(db_session):
    repo = PaymentRepository(db_session)
    society_id = uuid.uuid4()
    unit_id = uuid.uuid4()

    # Pre-create society and unit to satisfy FK
    society = SocietyModel(
        id=society_id,
        name="Rep Society",
        registration_no=f"REG/{uuid.uuid4().hex[:6]}",
        address="Address",
        city="City",
        state="State",
        country="India",
        zipcode="123456",
    )
    building = BuildingModel(id=uuid.uuid4(), society_id=society_id, name="Wing A")
    floor = FloorModel(id=uuid.uuid4(), building_id=building.id, floor_number=1)
    unit = UnitModel(id=unit_id, floor_id=floor.id, unit_number="A-101")
    db_session.add_all([society, building, floor, unit])
    await db_session.flush()

    invoice = MaintenanceInvoiceModel(
        society_id=society_id,
        unit_id=unit_id,
        billing_period="2026-10",
        title="Maintenance Oct 2026",
        amount=3000.0,
        due_date=datetime.now(timezone.utc) + timedelta(days=15),
        status=InvoiceStatus.PENDING.value,
    )
    saved = await repo.create_invoice(invoice)
    assert saved.id is not None
    assert saved.amount == 3000.0

    fetched = await repo.get_invoice_by_id(saved.id)
    assert fetched is not None
    assert fetched.billing_period == "2026-10"

    by_period = await repo.get_invoice_by_unit_and_period(unit_id, "2026-10")
    assert by_period is not None
    assert by_period.id == saved.id

    list_soc = await repo.list_invoices_by_society(society_id)
    assert len(list_soc) >= 1

    list_unit = await repo.list_invoices_by_unit(unit_id)
    assert len(list_unit) >= 1


@pytest.mark.asyncio
async def test_payment_repository_payments_and_receipts(db_session):
    repo = PaymentRepository(db_session)
    society_id = uuid.uuid4()
    user_id = uuid.uuid4()

    society = SocietyModel(
        id=society_id,
        name="Receipt Society",
        registration_no=f"REG/{uuid.uuid4().hex[:6]}",
        address="Address",
        city="City",
        state="State",
        country="India",
        zipcode="123456",
    )
    user = UserModel(
        user_id=user_id,
        first_name="Payer",
        last_name="One",
        role="resident",
    )
    db_session.add_all([society, user])
    await db_session.flush()

    payment = PaymentModel(
        society_id=society_id,
        user_id=user_id,
        amount=4500.0,
        payment_method=PaymentMethod.OFFLINE_UPI_NEFT.value,
        status=PaymentStatus.PENDING_APPROVAL.value,
        transaction_reference="UTR777888999",
    )
    saved_pay = await repo.create_payment(payment)
    assert saved_pay.id is not None

    pending_list = await repo.list_pending_approvals(society_id)
    assert len(pending_list) == 1
    assert pending_list[0].id == saved_pay.id

    # Create Receipt
    receipt = PaymentReceiptModel(
        payment_id=saved_pay.id,
        receipt_number="REC-202610-001",
        amount_paid=4500.0,
        issued_to_name="Payer One",
        unit_number="Unit 101",
        society_name="Receipt Society",
    )
    saved_rcp = await repo.create_receipt(receipt)
    assert saved_rcp.id is not None

    fetched_rcp = await repo.get_receipt_by_payment_id(saved_pay.id)
    assert fetched_rcp is not None
    assert fetched_rcp.receipt_number == "REC-202610-001"

    by_num = await repo.get_receipt_by_number("REC-202610-001")
    assert by_num is not None


# ============================================================================
# Service Tests
# ============================================================================

@pytest.mark.asyncio
async def test_invoice_service_create_invoice_success():
    mock_db = AsyncMock()
    mock_soc_repo = AsyncMock()
    mock_pay_repo = AsyncMock()

    soc_id = uuid.uuid4()
    unit_id = uuid.uuid4()

    mock_soc_repo.get_society.return_value = MagicMock(id=soc_id)
    mock_soc_repo.get_unit.return_value = MagicMock(id=unit_id, unit_number="B-202")
    mock_pay_repo.get_invoice_by_unit_and_period.return_value = None
    mock_pay_repo.create_invoice.side_effect = lambda inv: inv

    service = InvoiceService(
        db=mock_db,
        society_repo=mock_soc_repo,
        payment_repo=mock_pay_repo,
    )

    payload = InvoiceCreate(
        unit_id=unit_id,
        billing_period="2026-11",
        title="Nov 2026 Dues",
        amount=3500.0,
        due_date=datetime.now(timezone.utc) + timedelta(days=10),
    )

    result = await service.create_invoice(soc_id, payload)
    assert result.amount == 3500.0
    assert result.billing_period == "2026-11"
    mock_pay_repo.create_invoice.assert_called_once()


@pytest.mark.asyncio
async def test_invoice_service_create_invoice_duplicate_conflict():
    mock_db = AsyncMock()
    mock_soc_repo = AsyncMock()
    mock_pay_repo = AsyncMock()

    soc_id = uuid.uuid4()
    unit_id = uuid.uuid4()

    mock_soc_repo.get_society.return_value = MagicMock(id=soc_id)
    mock_soc_repo.get_unit.return_value = MagicMock(id=unit_id, unit_number="B-202")
    mock_pay_repo.get_invoice_by_unit_and_period.return_value = MagicMock(id=uuid.uuid4())

    service = InvoiceService(
        db=mock_db,
        society_repo=mock_soc_repo,
        payment_repo=mock_pay_repo,
    )

    payload = InvoiceCreate(
        unit_id=unit_id,
        billing_period="2026-11",
        title="Nov 2026 Dues",
        amount=3500.0,
        due_date=datetime.now(timezone.utc),
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_invoice(soc_id, payload)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_transaction_service_initiate_online_payment():
    mock_db = AsyncMock()
    mock_pay_repo = AsyncMock()

    inv_id = uuid.uuid4()
    soc_id = uuid.uuid4()
    user_id = uuid.uuid4()
    unit_id = uuid.uuid4()

    mock_inv = MagicMock(
        id=inv_id,
        society_id=soc_id,
        unit_id=unit_id,
        amount=3500.0,
        status=InvoiceStatus.PENDING.value,
    )
    mock_pay_repo.get_invoice_by_id.return_value = mock_inv
    mock_pay_repo.create_payment.side_effect = lambda p: p

    service = TransactionService(db=mock_db, payment_repo=mock_pay_repo)

    payload = InitiateOnlinePaymentRequest(
        invoice_id=inv_id,
        amount=3500.0,
        payment_method="online_mock",
    )

    res = await service.initiate_online_payment(user_id, soc_id, payload)
    assert res["status"] == "initiated"
    assert res["amount"] == 3500.0
    assert "gateway_order_id" in res


@pytest.mark.asyncio
async def test_transaction_service_submit_and_review_offline():
    mock_db = AsyncMock()
    mock_pay_repo = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_soc_repo = AsyncMock()

    inv_id = uuid.uuid4()
    soc_id = uuid.uuid4()
    user_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    mock_inv = MagicMock(
        id=inv_id,
        society_id=soc_id,
        unit_id=uuid.uuid4(),
        amount=4000.0,
        status=InvoiceStatus.PENDING.value,
    )
    mock_pay_repo.get_invoice_by_id.return_value = mock_inv
    mock_pay_repo.create_payment.side_effect = lambda p: p

    service = TransactionService(
        db=mock_db,
        payment_repo=mock_pay_repo,
        society_repo=mock_soc_repo,
        user_repo=mock_user_repo,
    )

    # 1. Submit offline
    sub_payload = SubmitOfflinePaymentRequest(
        invoice_id=inv_id,
        amount=4000.0,
        payment_method="offline_upi_neft",
        transaction_reference="UTR999111222",
    )
    sub_res = await service.submit_offline_payment(user_id, soc_id, sub_payload)
    assert sub_res.status == PaymentStatus.PENDING_APPROVAL.value
    assert sub_res.transaction_reference == "UTR999111222"

    # 2. Review & Approve
    mock_pay_repo.get_payment_by_id.return_value = sub_res
    mock_pay_repo.get_receipt_by_payment_id.return_value = None
    mock_user_repo.get_user_by_id.return_value = MagicMock(first_name="John", last_name="Resident")
    mock_soc_repo.get_society.return_value = MagicMock(name="Approved Society")
    mock_pay_repo.create_receipt.side_effect = lambda r: r
    mock_pay_repo.update_payment.side_effect = lambda p: p

    review_payload = ReviewOfflinePaymentRequest(approved=True)
    reviewed = await service.review_offline_payment(admin_id, sub_res.id, review_payload)
    assert reviewed.status == PaymentStatus.COMPLETED.value
    assert reviewed.approved_by == admin_id
    assert mock_inv.status == InvoiceStatus.PAID.value
    mock_pay_repo.create_receipt.assert_called_once()
