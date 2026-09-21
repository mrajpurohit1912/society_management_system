import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_complete_complaints_and_notices_lifecycle():
    # ------------------------------------------------------------------------
    # 1. Setup Society & Society Admin via Platform Provisioning
    # ------------------------------------------------------------------------
    soc_reg_no = f"RWA/CMP/{uuid.uuid4().hex[:6].upper()}"
    soc_payload = {
        "name": "Sapphire Enclave",
        "registration_no": soc_reg_no,
        "address": "45 Lotus Boulevard",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "zipcode": "500081",
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
            "first_name": "Suresh",
            "last_name": "Raina",
            "email": admin_email,
            "mobile": "+919876500000",
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
        json={"name": "Tower Alpha"},
        headers=admin_headers,
    )
    assert b_res.status_code == 201
    building_id = b_res.json()["data"]["id"]

    f_res = client.post(
        f"/api/v1/societies/{society_id}/buildings/{building_id}/floors",
        json={"floor_number": 4, "floor_name": "4th Floor"},
        headers=admin_headers,
    )
    assert f_res.status_code == 201
    floor_id = f_res.json()["data"]["id"]

    u_res = client.post(
        f"/api/v1/societies/{society_id}/buildings/{building_id}/floors/{floor_id}/units",
        json={"unit_number": "401"},
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
            "first_name": "Kavita",
            "last_name": "Krishnamurthy",
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

    # Resident requests membership for Unit 401
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
    # 4. Complaints Lifecycle Flow
    # ------------------------------------------------------------------------
    # Resident reports P1 plumbing issue
    complaint_payload = {
        "unit_id": unit_id,
        "title": "Severe pipe leakage in kitchen",
        "description": "Kitchen sink main drain line is broken and flooding the floor.",
        "category": "plumbing",
        "scope": "personal_unit",
        "priority": "p1_critical",
        "photos": ["https://s3.amazonaws.com/test/leak.jpg"],
    }
    tkt_res = client.post(
        f"/api/v1/societies/{society_id}/complaints",
        json=complaint_payload,
        headers=resident_headers,
    )
    assert tkt_res.status_code == 201
    ticket = tkt_res.json()
    ticket_id = ticket["id"]
    assert ticket["status"] == "open"
    assert ticket["priority"] == "p1_critical"
    assert ticket["ticket_number"].startswith("TKT-")
    assert ticket["sla_deadline"] is not None

    # Resident views their tickets
    my_tkts = client.get(
        f"/api/v1/societies/{society_id}/complaints/my",
        headers=resident_headers,
    )
    assert my_tkts.status_code == 200
    assert len(my_tkts.json()) >= 1
    assert any(t["id"] == ticket_id for t in my_tkts.json())

    # Resident adds comment
    comment_res = client.post(
        f"/api/v1/societies/{society_id}/complaints/{ticket_id}/comments",
        json={"comment": "I have turned off the main inlet valve temporarily."},
        headers=resident_headers,
    )
    assert comment_res.status_code == 201

    # Admin views tickets
    admin_tkts = client.get(
        f"/api/v1/societies/{society_id}/complaints?category=plumbing",
        headers=admin_headers,
    )
    assert admin_tkts.status_code == 200
    assert len(admin_tkts.json()) >= 1

    # Admin assigns vendor
    assign_res = client.post(
        f"/api/v1/societies/{society_id}/complaints/{ticket_id}/assign",
        json={
            "assigned_vendor_name": "HydroFix Emergency Plumbers",
            "assigned_vendor_phone": "+919876543210",
            "notes": "Emergency dispatch; will arrive by 3 PM.",
        },
        headers=admin_headers,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "assigned"
    assert assign_res.json()["assigned_vendor_name"] == "HydroFix Emergency Plumbers"

    # Admin marks in progress
    prog_res = client.patch(
        f"/api/v1/societies/{society_id}/complaints/{ticket_id}/status",
        json={"status": "in_progress", "notes": "Plumber is dismantling pipe."},
        headers=admin_headers,
    )
    assert prog_res.status_code == 200
    assert prog_res.json()["status"] == "in_progress"

    # Admin marks resolved
    resolve_res = client.post(
        f"/api/v1/societies/{society_id}/complaints/{ticket_id}/resolve",
        json={
            "resolution_notes": "Fitted new PVC drain trap and sealed joints with waterproof adhesive.",
            "resolution_photos": ["https://s3.amazonaws.com/test/fixed.jpg"],
        },
        headers=admin_headers,
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"
    assert resolve_res.json()["resolved_at"] is not None

    # Resident closes ticket and leaves 5-star rating
    close_res = client.post(
        f"/api/v1/societies/{society_id}/complaints/{ticket_id}/close",
        json={
            "resident_rating": 5,
            "resident_feedback": "Excellent speed and workmanship by the plumber!",
        },
        headers=resident_headers,
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"
    assert close_res.json()["resident_rating"] == 5

    # Admin views summary metrics
    summary_res = client.get(
        f"/api/v1/societies/{society_id}/complaints/summary",
        headers=admin_headers,
    )
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["closed_tickets"] >= 1
    assert summary["average_rating"] == 5.0

    # ------------------------------------------------------------------------
    # 5. Notice Board Lifecycle Flow
    # ------------------------------------------------------------------------
    # Admin publishes urgent AGM notice
    notice_payload = {
        "title": "Emergency AGM - Water Harvesting Proposal",
        "content": "All owners and residents are requested to join Sunday 11 AM in Clubhouse.",
        "category": "meeting_agm",
        "priority": "urgent",
        "target_audience": "all",
        "is_pinned": True,
        "attachments": ["https://s3.amazonaws.com/test/agm_agenda.pdf"],
    }
    notice_res = client.post(
        f"/api/v1/societies/{society_id}/notices",
        json=notice_payload,
        headers=admin_headers,
    )
    assert notice_res.status_code == 201
    notice = notice_res.json()
    notice_id = notice["id"]
    assert notice["is_pinned"] is True

    # Resident lists active notices (pinned notice is returned)
    res_notices = client.get(
        f"/api/v1/societies/{society_id}/notices",
        headers=resident_headers,
    )
    assert res_notices.status_code == 200
    assert len(res_notices.json()) >= 1
    assert any(n["id"] == notice_id for n in res_notices.json())

    # Resident views notice details (auto-marks read receipt)
    view_notice = client.get(
        f"/api/v1/societies/{society_id}/notices/{notice_id}",
        headers=resident_headers,
    )
    assert view_notice.status_code == 200
    assert view_notice.json()["is_read_by_me"] is True
    assert view_notice.json()["read_count"] >= 1

    # Admin checks audit read stats
    stats_res = client.get(
        f"/api/v1/societies/{society_id}/notices/{notice_id}/receipts",
        headers=admin_headers,
    )
    assert stats_res.status_code == 200
    assert stats_res.json()["total_reads"] >= 1

    # Admin updates notice
    patch_res = client.patch(
        f"/api/v1/societies/{society_id}/notices/{notice_id}",
        json={"title": "Updated: Emergency AGM - Water Harvesting Proposal"},
        headers=admin_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"].startswith("Updated:")

    # Admin deletes notice
    del_res = client.delete(
        f"/api/v1/societies/{society_id}/notices/{notice_id}",
        headers=admin_headers,
    )
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True
