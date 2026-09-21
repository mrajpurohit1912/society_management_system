import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_complete_visitor_and_gatekeeper_management_lifecycle():
    # ------------------------------------------------------------------------
    # 1. Setup Society & Society Admin via Platform Provisioning
    # ------------------------------------------------------------------------
    soc_reg_no = f"RWA/VIS/{uuid.uuid4().hex[:6].upper()}"
    soc_payload = {
        "name": "Greenwood Valley",
        "registration_no": soc_reg_no,
        "address": "123 Outer Ring Rd",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "zipcode": "560103",
    }
    soc_res = client.post("/api/v1/platform/societies", json=soc_payload)
    assert soc_res.status_code == 201
    society_id = soc_res.json()["data"]["society_id"]

    # Attach subscription
    client.post(
        "/api/v1/platform/subscriptions",
        json={
            "society_id": society_id,
            "plan": "GOLD",
            "valid_months": 12,
            "max_admins": 5,
            "max_storage_gb": 10,
        },
    )

    # Provision Admin
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    admin_res = client.post(
        "/api/v1/platform/admins",
        json={
            "society_id": society_id,
            "first_name": "Ramesh",
            "last_name": "Sharma",
            "email": admin_email,
            "mobile": "+919876543210",
        },
    )
    assert admin_res.status_code == 201
    token = admin_res.json()["data"]["activation_token"]

    # Activate & Login Admin
    client.post(
        "/api/v1/auth/activate",
        json={"token": token, "password": "AdminPassword123!"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "AdminPassword123!"},
    )
    admin_jwt = login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_jwt}"}

    # ------------------------------------------------------------------------
    # 2. Setup Building, Floor, and Unit
    # ------------------------------------------------------------------------
    b_res = client.post(
        f"/api/v1/societies/{society_id}/buildings",
        json={"name": "Tower C"},
        headers=admin_headers,
    )
    assert b_res.status_code == 201
    building_id = b_res.json()["data"]["id"]

    f_res = client.post(
        f"/api/v1/societies/{society_id}/buildings/{building_id}/floors",
        json={"floor_number": 5, "floor_name": "5th Floor"},
        headers=admin_headers,
    )
    assert f_res.status_code == 201
    floor_id = f_res.json()["data"]["id"]

    u_res = client.post(
        f"/api/v1/societies/{society_id}/buildings/{building_id}/floors/{floor_id}/units",
        json={"unit_number": "502"},
        headers=admin_headers,
    )
    assert u_res.status_code == 201
    unit_id = u_res.json()["data"]["id"]

    # ------------------------------------------------------------------------
    # 3. Create & Onboard Resident
    # ------------------------------------------------------------------------
    resident_email = f"resident_{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/v1/auth/resident/signup",
        json={
            "first_name": "Aarav",
            "last_name": "Kapoor",
            "email": resident_email,
            "password": "ResidentPassword123!",
        },
    )
    res_login = client.post(
        "/api/v1/auth/login",
        json={"email": resident_email, "password": "ResidentPassword123!"},
    )
    resident_jwt = res_login.json()["data"]["access_token"]
    resident_headers = {"Authorization": f"Bearer {resident_jwt}"}

    # Resident requests membership for Unit 502
    req_res = client.post(
        "/api/v1/societies/membership/request",
        json={
            "society_id": society_id,
            "unit_id": unit_id,
            "role": "resident",
        },
        headers=resident_headers,
    )
    assert req_res.status_code == 201
    membership_id = req_res.json()["data"]["membership_id"]

    # Admin approves resident membership
    appr_res = client.post(
        f"/api/v1/societies/{society_id}/membership/{membership_id}/approve",
        headers=admin_headers,
    )
    assert appr_res.status_code == 200

    # ------------------------------------------------------------------------
    # 4. Create & Onboard Security Guard
    # ------------------------------------------------------------------------
    guard_email = f"guard_{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/v1/auth/resident/signup",
        json={
            "first_name": "Bhim",
            "last_name": "Singh",
            "email": guard_email,
            "password": "GuardPassword123!",
        },
    )
    guard_login = client.post(
        "/api/v1/auth/login",
        json={"email": guard_email, "password": "GuardPassword123!"},
    )
    guard_jwt = guard_login.json()["data"]["access_token"]
    guard_headers = {"Authorization": f"Bearer {guard_jwt}"}

    # Guard requests membership with security role
    guard_req = client.post(
        "/api/v1/societies/membership/request",
        json={
            "society_id": society_id,
            "role": "security",
        },
        headers=guard_headers,
    )
    assert guard_req.status_code == 201
    guard_membership_id = guard_req.json()["data"]["membership_id"]

    # Admin approves guard membership
    guard_appr = client.post(
        f"/api/v1/societies/{society_id}/membership/{guard_membership_id}/approve",
        headers=admin_headers,
    )
    assert guard_appr.status_code == 200

    # ------------------------------------------------------------------------
    # 5. Resident Pre-Approves Guest Pass (Passcode & QR)
    # ------------------------------------------------------------------------
    pass_payload = {
        "unit_id": unit_id,
        "visitor_name": "Siddharth Malhotra",
        "visitor_phone": "+919876541234",
        "visitor_type": "guest",
        "valid_hours": 12,
        "vehicle_number": "KA03MM1234",
        "notes": "Family friend visiting for dinner",
    }
    pass_res = client.post(
        f"/api/v1/societies/{society_id}/visitor-passes",
        json=pass_payload,
        headers=resident_headers,
    )
    assert pass_res.status_code == 201
    pass_data = pass_res.json()
    pass_id = pass_data["id"]
    passcode = pass_data["passcode"]
    qr_token = pass_data["qr_code_token"]
    assert len(passcode) == 6
    assert passcode.isdigit()
    assert pass_data["status"] == "active"

    # List resident's passes
    list_passes = client.get(
        f"/api/v1/societies/{society_id}/visitor-passes",
        headers=resident_headers,
    )
    assert list_passes.status_code == 200
    assert len(list_passes.json()) >= 1
    assert any(p["id"] == pass_id for p in list_passes.json())

    # Get single pass details
    single_pass = client.get(
        f"/api/v1/societies/{society_id}/visitor-passes/{pass_id}",
        headers=resident_headers,
    )
    assert single_pass.status_code == 200
    assert single_pass.json()["visitor_name"] == "Siddharth Malhotra"

    # ------------------------------------------------------------------------
    # 6. Gatekeeper Verifies Passcode & Checks In Visitor
    # ------------------------------------------------------------------------
    checkin_res = client.post(
        f"/api/v1/societies/{society_id}/gatekeeper/verify-passcode",
        json={
            "passcode": passcode,
            "gate_number": "Gate 1 - North",
        },
        headers=guard_headers,
    )
    assert checkin_res.status_code == 200
    log_data = checkin_res.json()
    log_id = log_data["id"]
    assert log_data["status"] == "inside"
    assert log_data["entry_type"] == "pre_approved"
    assert log_data["visitor_name"] == "Siddharth Malhotra"

    # Verifying again with same passcode should fail (completed pass)
    repeat_res = client.post(
        f"/api/v1/societies/{society_id}/gatekeeper/verify-passcode",
        json={"passcode": passcode},
        headers=guard_headers,
    )
    assert repeat_res.status_code == 404

    # ------------------------------------------------------------------------
    # 7. Check Active Visitors List
    # ------------------------------------------------------------------------
    active_res = client.get(
        f"/api/v1/societies/{society_id}/gatekeeper/active",
        headers=guard_headers,
    )
    assert active_res.status_code == 200
    active_list = active_res.json()
    assert any(l["id"] == log_id for l in active_list)

    # ------------------------------------------------------------------------
    # 8. Gatekeeper Checks Out the Visitor
    # ------------------------------------------------------------------------
    checkout_res = client.post(
        f"/api/v1/societies/{society_id}/gatekeeper/logs/{log_id}/checkout",
        json={"gate_number": "Gate 1 - North"},
        headers=guard_headers,
    )
    assert checkout_res.status_code == 200
    assert checkout_res.json()["status"] == "checked_out"
    assert checkout_res.json()["check_out_time"] is not None

    # Checking out again should fail (status is already checked_out)
    repeat_checkout = client.post(
        f"/api/v1/societies/{society_id}/gatekeeper/logs/{log_id}/checkout",
        json={},
        headers=guard_headers,
    )
    assert repeat_checkout.status_code == 400

    # ------------------------------------------------------------------------
    # 9. Gatekeeper Quick Check-in (Delivery Agent)
    # ------------------------------------------------------------------------
    quick_res = client.post(
        f"/api/v1/societies/{society_id}/gatekeeper/quick-checkin",
        json={
            "unit_id": unit_id,
            "visitor_name": "Rohan Zomato",
            "visitor_phone": "+919888877777",
            "visitor_type": "delivery",
            "company_name": "Zomato",
            "vehicle_number": "KA01EV5678",
            "gate_number": "Gate 2",
        },
        headers=guard_headers,
    )
    assert quick_res.status_code == 201
    quick_log = quick_res.json()
    assert quick_log["entry_type"] == "quick_checkin"
    assert quick_log["status"] == "inside"
    assert quick_log["company_name"] == "Zomato"

    # ------------------------------------------------------------------------
    # 10. Gatekeeper Dashboard Summary
    # ------------------------------------------------------------------------
    summary_res = client.get(
        f"/api/v1/societies/{society_id}/gatekeeper/summary",
        headers=guard_headers,
    )
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_inside"] >= 1
    assert summary["deliveries_inside"] >= 1

    # ------------------------------------------------------------------------
    # 11. QR Code Verification Flow & Pass Revocation
    # ------------------------------------------------------------------------
    # Resident generates a 2nd pass for another guest
    pass2_res = client.post(
        f"/api/v1/societies/{society_id}/visitor-passes",
        json={
            "unit_id": unit_id,
            "visitor_name": "Priya Sharma",
            "visitor_phone": "+919111122222",
            "visitor_type": "guest",
        },
        headers=resident_headers,
    )
    assert pass2_res.status_code == 201
    pass2_id = pass2_res.json()["id"]
    qr2_token = pass2_res.json()["qr_code_token"]

    # Resident generates a 3rd pass to test revocation
    pass3_res = client.post(
        f"/api/v1/societies/{society_id}/visitor-passes",
        json={
            "unit_id": unit_id,
            "visitor_name": "Revoke Candidate",
            "visitor_phone": "+919333344444",
            "visitor_type": "guest",
        },
        headers=resident_headers,
    )
    assert pass3_res.status_code == 201
    pass3_id = pass3_res.json()["id"]

    # Resident revokes Pass 3
    revoke_res = client.delete(
        f"/api/v1/societies/{society_id}/visitor-passes/{pass3_id}",
        headers=resident_headers,
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "revoked"

    # Guard checks in Pass 2 via QR code
    qr_checkin = client.post(
        f"/api/v1/societies/{society_id}/gatekeeper/verify-qr",
        json={"qr_token": qr2_token, "gate_number": "Gate 1 - North"},
        headers=guard_headers,
    )
    assert qr_checkin.status_code == 200
    assert qr_checkin.json()["status"] == "inside"
    assert qr_checkin.json()["visitor_name"] == "Priya Sharma"

    # ------------------------------------------------------------------------
    # 12. Query Visitor History Logs
    # ------------------------------------------------------------------------
    history_res = client.get(
        f"/api/v1/societies/{society_id}/gatekeeper/logs?status=inside",
        headers=guard_headers,
    )
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 2
