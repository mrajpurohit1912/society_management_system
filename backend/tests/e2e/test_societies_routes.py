import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_platform_admin, require_society_admin
from app.societies.models import SocietyRole

# --- Fixtures ---

@pytest.fixture
def mock_db():
    from sqlalchemy.ext.asyncio import AsyncSession
    session = AsyncMock(spec=AsyncSession)
    session.begin = MagicMock()
    session.begin.return_value.__aenter__ = AsyncMock()
    session.begin.return_value.__aexit__ = AsyncMock(return_value=False)
    return session


@pytest.fixture
def mock_normal_user():
    user = MagicMock()
    user.user_id = uuid.uuid4()
    user.first_name = "Jane"
    user.last_name = "Doe"
    user.role = "member"
    return user


@pytest.fixture
def mock_platform_admin():
    user = MagicMock()
    user.user_id = uuid.uuid4()
    user.first_name = "Super"
    user.last_name = "Admin"
    user.role = "admin"
    return user


@pytest.fixture
def test_client(mock_db, mock_normal_user):
    # Setup standard overrides
    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_normal_user
    
    # By default, mock require_society_admin to allow the action
    # Specific tests will override this behavior
    async def mock_soc_admin(society_id: uuid.UUID):
        return mock_normal_user
    app.dependency_overrides[require_society_admin] = mock_soc_admin

    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.clear()


# --- Tests ---

@patch("app.societies.routes.SocietyService")
def test_create_society_as_platform_admin(mock_service_cls, test_client, mock_platform_admin):
    """
    Test that a platform admin can successfully create a new society.
    """
    # Overwrite dependency specifically for platform admin check
    app.dependency_overrides[require_platform_admin] = lambda: mock_platform_admin
    
    # Setup mock service
    mock_service = AsyncMock()
    mock_society = MagicMock()
    mock_society.id = uuid.uuid4()
    mock_society.name = "Palm Heights"
    mock_society.registration_no = "PH-992"
    mock_society.address = "123 Palm Ave"
    mock_society.city = "Miami"
    mock_society.state = "FL"
    mock_society.country = "USA"
    mock_society.zipcode = "33101"
    mock_society.email = "info@palmheights.com"
    mock_society.phone = "1234567890"
    mock_society.status = "active"
    mock_society.created_at = datetime.now()
    mock_society.updated_at = datetime.now()
    
    mock_service.create_society.return_value = mock_society
    mock_service_cls.return_value = mock_service

    payload = {
        "name": "Palm Heights",
        "registration_no": "PH-992",
        "address": "123 Palm Ave",
        "city": "Miami",
        "state": "FL",
        "country": "USA",
        "zipcode": "33101",
        "email": "info@palmheights.com",
        "phone": "1234567890"
    }

    response = test_client.post("/api/v1/societies", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Palm Heights"
    assert data["registration_no"] == "PH-992"


def test_create_society_as_normal_user_forbidden(test_client):
    """
    Test that a normal user cannot create a society (returns 403).
    """
    # Overwrite platform admin dependency to raise 403
    def mock_fail_platform_admin():
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Forbidden")
    app.dependency_overrides[require_platform_admin] = mock_fail_platform_admin

    payload = {
        "name": "Palm Heights",
        "registration_no": "PH-992",
        "address": "123 Palm Ave",
        "city": "Miami",
        "state": "FL",
        "country": "USA",
        "zipcode": "33101"
    }

    response = test_client.post("/api/v1/societies", json=payload)
    assert response.status_code == 403


@patch("app.societies.routes.BuildingService")
def test_create_building_success(mock_service_cls, test_client, mock_normal_user):
    """
    Test building creation inside a society.
    """
    mock_service = AsyncMock()
    mock_building = MagicMock()
    mock_building.id = uuid.uuid4()
    mock_building.society_id = uuid.uuid4()
    mock_building.name = "Tower A"
    mock_building.created_at = datetime.now()
    
    mock_service.create_building.return_value = mock_building
    mock_service_cls.return_value = mock_service

    payload = {"name": "Tower A"}
    soc_id = uuid.uuid4()

    response = test_client.post(f"/api/v1/societies/{soc_id}/buildings", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tower A"


@patch("app.societies.routes.BulkProvisionService")
def test_bulk_provision_success(mock_service_cls, test_client):
    """
    Test bulk provisioning of physical layout.
    """
    mock_service = AsyncMock()
    
    mock_building = MagicMock()
    mock_building.id = uuid.uuid4()
    mock_building.society_id = uuid.uuid4()
    mock_building.name = "Tower A"
    mock_building.created_at = datetime.now()
    
    mock_service.provision_society_structure.return_value = [mock_building]
    mock_service_cls.return_value = mock_service

    payload = {
        "buildings": [
            {
                "name": "Tower A",
                "number_of_floors": 5,
                "units_per_floor": 4
            }
        ]
    }
    soc_id = uuid.uuid4()

    response = test_client.post(f"/api/v1/societies/{soc_id}/provision", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Tower A"
