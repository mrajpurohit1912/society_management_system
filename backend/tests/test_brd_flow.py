import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_complete_brd_enterprise_flow():
    # 1. Register Society Lead (Public)
    lead_payload = {
        "organization_name": "Sunshine Residency RWA",
        "primary_contact_name": "Mahavir Lead",
        "email": "delivered@resend.dev",
        "mobile": "+919999988888",
        "city": "Mumbai",
        "expected_flats": 120,
        "expected_admins": 3,
        "comments": "Interested in Enterprise Plan"
    }
    lead_res = client.post("/api/v1/register-society", json=lead_payload)
    assert lead_res.status_code == 201
    assert lead_res.json()["success"] is True

    # 2. Platform Admin Provisioning: Create Society
    society_payload = {
        "name": "Sunshine Residency",
        "registration_no": f"RWA/MUM/{uuid.uuid4().hex[:6]}",
        "address": "123 Palm Grove, Bandra",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "zipcode": "400050"
    }
    soc_res = client.post("/api/v1/platform/societies", json=society_payload)
    assert soc_res.status_code == 201
    society_id = soc_res.json()["data"]["society_id"]

    # 3. Platform Admin Provisioning: Create Subscription
    sub_payload = {
        "society_id": society_id,
        "plan": "GOLD",
        "valid_months": 12,
        "max_admins": 5,
        "max_storage_gb": 20
    }
    sub_res = client.post("/api/v1/platform/subscriptions", json=sub_payload)
    assert sub_res.status_code == 201
    assert sub_res.json()["data"]["status"] == "active"

    # 4. Platform Admin Provisioning: Create Primary Society Admin
    admin_payload = {
        "society_id": society_id,
        "first_name": "Admin",
        "last_name": "User",
        "email": f"admin_{uuid.uuid4().hex[:6]}@resend.dev",
        "mobile": "+919876543210"
    }
    admin_res = client.post("/api/v1/platform/admins", json=admin_payload)
    assert admin_res.status_code == 201
    activation_token = admin_res.json()["data"]["activation_token"]
    admin_email = admin_payload["email"]

    # 5. Admin Set Password & Activate Account
    act_res = client.post("/api/v1/auth/activate", json={
        "token": activation_token,
        "password": "AdminSecurePassword123!"
    })
    assert act_res.status_code == 200
    assert act_res.json()["data"]["status"] == "active"

    # 6. Admin Login
    admin_login_res = client.post("/api/v1/auth/login", json={
        "email": admin_email,
        "password": "AdminSecurePassword123!"
    })
    assert admin_login_res.status_code == 200
    admin_jwt = admin_login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_jwt}"}

    # 7. Resident Public Signup
    resident_email = f"resident_{uuid.uuid4().hex[:6]}@resend.dev"
    res_signup_res = client.post("/api/v1/auth/resident/signup", json={
        "first_name": "Jane",
        "last_name": "Resident",
        "email": resident_email,
        "password": "ResidentPassword123!"
    })
    assert res_signup_res.status_code == 201
    assert res_signup_res.json()["data"]["status"] == "registered"

    # 8. Resident Login (Before Membership)
    res_login_res = client.post("/api/v1/auth/login", json={
        "email": resident_email,
        "password": "ResidentPassword123!"
    })
    assert res_login_res.status_code == 200
    resident_jwt = res_login_res.json()["data"]["access_token"]
    resident_headers = {"Authorization": f"Bearer {resident_jwt}"}

    # 9. Resident Request Membership to Sunshine Residency
    mem_req_res = client.post("/api/v1/societies/membership/request", json={
        "society_id": society_id,
        "role": "resident"
    }, headers=resident_headers)
    assert mem_req_res.status_code == 201
    membership_id = mem_req_res.json()["data"]["membership_id"]
    assert mem_req_res.json()["data"]["status"] == "pending"

    # 10. Society Admin List Pending Requests & Approve
    pending_res = client.get(f"/api/v1/societies/{society_id}/membership/requests", headers=admin_headers)
    assert pending_res.status_code == 200
    assert len(pending_res.json()["data"]) >= 1

    approve_res = client.post(f"/api/v1/societies/{society_id}/membership/{membership_id}/approve", headers=admin_headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["data"]["status"] == "approved"
