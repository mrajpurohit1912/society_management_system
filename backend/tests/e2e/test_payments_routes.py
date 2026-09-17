import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_complete_payments_and_billing_lifecycle():
    # ------------------------------------------------------------------------
    # 1. Setup Society & Society Admin via Platform Provisioning
    # ------------------------------------------------------------------------
    soc_reg_no = f"RWA/PAY/{uuid.uuid4().hex[:6].upper()}"
    soc_payload = {
        "name": "Palm Residency",
        "registration_no": soc_reg_no,
        "address": "456 Marine Drive",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "zipcode": "400020",
    }
    soc_res = client.post("/api/v1/platform/societies", json=soc_payload)
    assert soc_res.status_code == 201
    society_id = soc_res.json()["data"]["society_id"]

    # Attach subscription
    client.post("/api/v1/platform/subscriptions", json={
        "society_id": society_id,
        "plan": "GOLD",
        "valid_months": 12,
        "max_admins": 5,
        "max_storage_gb": 10,
    })

    # Create Admin
    admin_email = f"treasurer_{uuid.uuid4().hex[:6]}@example.com"
    admin_res = client.post("/api/v1/platform/admins", json={
        "society_id": society_id,
        "first_name": "Rajesh",
        "last_name": "Treasurer",
        "email": admin_email,
        "mobile": "+919876543210",
    })
    assert admin_res.status_code == 201
    token = admin_res.json()["data"]["activation_token"]

    # Activate & Login Admin
    client.post("/api/v1/auth/activate", json={"token": token, "password": "AdminPassword123!"})
    login_res = client.post("/api/v1/auth/login", json={"email": admin_email, "password": "AdminPassword123!"})
    admin_jwt = login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_jwt}"}

    # ------------------------------------------------------------------------
    # 2. Setup Building, Floor, and Units
    # ------------------------------------------------------------------------
    b_res = client.post(f"/api/v1/societies/{society_id}/buildings", json={"name": "Tower A"}, headers=admin_headers)
    building_id = b_res.json()["data"]["id"]

    f_res = client.post(f"/api/v1/societies/{society_id}/buildings/{building_id}/floors", json={"floor_number": 1, "floor_name": "1st Floor"}, headers=admin_headers)
    assert f_res.status_code == 201
    floor_id = f_res.json()["data"]["id"]

    u1_res = client.post(f"/api/v1/societies/{society_id}/buildings/{building_id}/floors/{floor_id}/units", json={"unit_number": "101"}, headers=admin_headers)
    assert u1_res.status_code == 201
    unit1_id = u1_res.json()["data"]["id"]

    u2_res = client.post(f"/api/v1/societies/{society_id}/buildings/{building_id}/floors/{floor_id}/units", json={"unit_number": "102"}, headers=admin_headers)
    assert u2_res.status_code == 201
    unit2_id = u2_res.json()["data"]["id"]

    # ------------------------------------------------------------------------
    # 3. Create Single Invoice for Unit 101
    # ------------------------------------------------------------------------
    due_date = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    inv_res = client.post(
        f"/api/v1/societies/{society_id}/invoices",
        json={
            "unit_id": unit1_id,
            "billing_period": "2026-10",
            "title": "Maintenance Oct 2026",
            "description": "Standard monthly maintenance fees",
            "amount": 3500.0,
            "due_date": due_date,
        },
        headers=admin_headers,
    )
    assert inv_res.status_code == 201
    invoice1_id = inv_res.json()["id"]
    assert inv_res.json()["status"] == "pending"
    assert inv_res.json()["amount"] == 3500.0

    # ------------------------------------------------------------------------
    # 4. Create Resident User & Login
    # ------------------------------------------------------------------------
    resident_email = f"resident_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/resident/signup", json={
        "first_name": "Sunita",
        "last_name": "Patel",
        "email": resident_email,
        "password": "ResidentPassword123!",
    })
    res_login = client.post("/api/v1/auth/login", json={"email": resident_email, "password": "ResidentPassword123!"})
    resident_jwt = res_login.json()["data"]["access_token"]
    resident_headers = {"Authorization": f"Bearer {resident_jwt}"}

    # ------------------------------------------------------------------------
    # 5. Resident Views Unit Dues
    # ------------------------------------------------------------------------
    dues_res = client.get(f"/api/v1/units/{unit1_id}/dues", headers=resident_headers)
    assert dues_res.status_code == 200
    assert len(dues_res.json()) >= 1
    assert dues_res.json()[0]["id"] == invoice1_id

    # ------------------------------------------------------------------------
    # 6. Online Payment Flow (Mock Gateway Checkout & Verification)
    # ------------------------------------------------------------------------
    init_res = client.post(
        f"/api/v1/societies/{society_id}/payments/initiate",
        json={
            "invoice_id": invoice1_id,
            "amount": 3500.0,
            "payment_method": "online_mock",
        },
        headers=resident_headers,
    )
    assert init_res.status_code == 201
    init_data = init_res.json()
    payment1_id = init_data["payment_id"]
    gateway_order_id = init_data["gateway_order_id"]
    assert init_data["status"] == "initiated"

    # Verify Online Payment
    verify_res = client.post(
        "/api/v1/payments/verify",
        json={
            "payment_id": payment1_id,
            "gateway_order_id": gateway_order_id,
            "gateway_payment_id": "pay_mock_success_999",
            "gateway_signature": "mock_valid_signature",
        },
        headers=resident_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["success"] is True
    assert verify_res.json()["status"] == "completed"
    receipt_num1 = verify_res.json()["receipt_number"]
    assert receipt_num1.startswith("REC-")

    # Check Invoice 1 status is now PAID
    inv_check = client.get(f"/api/v1/societies/{society_id}/invoices/{invoice1_id}", headers=resident_headers)
    assert inv_check.status_code == 200
    assert inv_check.json()["status"] == "paid"

    # ------------------------------------------------------------------------
    # 7. Bulk Generate Invoices for Next Month (Nov 2026)
    # ------------------------------------------------------------------------
    bulk_res = client.post(
        f"/api/v1/societies/{society_id}/invoices/bulk-generate",
        json={
            "billing_period": "2026-11",
            "title": "Maintenance Nov 2026",
            "amount": 3800.0,
            "due_date_days": 15,
        },
        headers=admin_headers,
    )
    assert bulk_res.status_code == 201
    bulk_invoices = bulk_res.json()
    assert len(bulk_invoices) == 2  # Unit 101 and 102
    invoice2_id = next(inv["id"] for inv in bulk_invoices if inv["unit_id"] == unit1_id)

    # ------------------------------------------------------------------------
    # 8. Offline Payment Flow (Resident Submits UTR, Admin Approves)
    # ------------------------------------------------------------------------
    offline_submit_res = client.post(
        f"/api/v1/societies/{society_id}/payments/submit-offline",
        json={
            "invoice_id": invoice2_id,
            "amount": 3800.0,
            "payment_method": "offline_upi_neft",
            "transaction_reference": "UTR9876543210",
            "description": "Paid via Google Pay to society HDFC account",
        },
        headers=resident_headers,
    )
    assert offline_submit_res.status_code == 201
    offline_data = offline_submit_res.json()
    payment2_id = offline_data["id"]
    assert offline_data["status"] == "pending_approval"
    assert offline_data["transaction_reference"] == "UTR9876543210"

    # Admin checks pending approval queue
    pending_res = client.get(f"/api/v1/societies/{society_id}/payments/pending-approval", headers=admin_headers)
    assert pending_res.status_code == 200
    assert any(p["id"] == payment2_id for p in pending_res.json())

    # Admin Approves the offline payment
    review_res = client.post(
        f"/api/v1/societies/{society_id}/payments/{payment2_id}/review",
        json={"approved": True},
        headers=admin_headers,
    )
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "completed"

    # Invoice 2 is now PAID
    inv2_check = client.get(f"/api/v1/societies/{society_id}/invoices/{invoice2_id}", headers=resident_headers)
    assert inv2_check.json()["status"] == "paid"

    # ------------------------------------------------------------------------
    # 9. Download / View Official Receipt
    # ------------------------------------------------------------------------
    rcp_res = client.get(f"/api/v1/payments/{payment2_id}/receipt", headers=resident_headers)
    assert rcp_res.status_code == 200
    assert rcp_res.json()["amount_paid"] == 3800.0
    assert rcp_res.json()["society_name"] == "Palm Residency"
    assert rcp_res.json()["receipt_number"].startswith("REC-")

    # ------------------------------------------------------------------------
    # 10. Society Admin Collection Summary
    # ------------------------------------------------------------------------
    summary_res = client.get(f"/api/v1/societies/{society_id}/collection-summary", headers=admin_headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    # Invoiced: 3500 (Oct unit 101) + 3800 (Nov unit 101) + 3800 (Nov unit 102) = 11100
    assert summary["total_invoiced"] == 11100.0
    # Collected: 3500 (Oct unit 101) + 3800 (Nov unit 101) = 7300
    assert summary["total_collected"] == 7300.0
    assert summary["pending_approval_count"] == 0
