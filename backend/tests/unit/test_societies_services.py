import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime
from fastapi import HTTPException

from app.societies.services import (
    SocietyService,
    BuildingService,
    FloorService,
    UnitService,
    ResidentService,
    VehicleService,
    BulkProvisionService
)
from app.societies.schemas import (
    SocietyCreate,
    BuildingCreate,
    FloorCreate,
    UnitCreate,
    ResidentAssign,
    VehicleRegister,
    BulkProvisionRequest,
    BuildingProvision
)
from app.societies.models import SocietyStatus, UnitType, UnitStatus, ResidencyType, ResidentStatus, VehicleType

# --- Society Service Tests ---

@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_create_society_success(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_society_by_reg_no.return_value = None
    
    mock_society = MagicMock()
    mock_repo.create_society.return_value = mock_society
    mock_repo_cls.return_value = mock_repo
    
    service = SocietyService(mock_db)
    payload = SocietyCreate(
        name="Sunshine Residency",
        registration_no="SR-101",
        address="1 Main St",
        city="Houston",
        state="TX",
        country="USA",
        zipcode="77001"
    )
    
    result = await service.create_society(payload)
    mock_repo.get_society_by_reg_no.assert_called_once_with("SR-101")
    mock_repo.create_society.assert_called_once_with(payload)
    assert result == mock_society


@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_create_society_already_exists(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_society_by_reg_no.return_value = MagicMock()
    mock_repo_cls.return_value = mock_repo
    
    service = SocietyService(mock_db)
    payload = SocietyCreate(
        name="Sunshine Residency",
        registration_no="SR-101",
        address="1 Main St",
        city="Houston",
        state="TX",
        country="USA",
        zipcode="77001"
    )
    
    with pytest.raises(HTTPException) as exc:
        await service.create_society(payload)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_get_society_success(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_society = MagicMock()
    mock_repo.get_society.return_value = mock_society
    mock_repo_cls.return_value = mock_repo
    
    service = SocietyService(mock_db)
    soc_id = uuid.uuid4()
    
    result = await service.get_society(soc_id)
    mock_repo.get_society.assert_called_once_with(soc_id)
    assert result == mock_society


@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_get_society_not_found(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_society.return_value = None
    mock_repo_cls.return_value = mock_repo
    
    service = SocietyService(mock_db)
    soc_id = uuid.uuid4()
    
    with pytest.raises(HTTPException) as exc:
        await service.get_society(soc_id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_list_societies(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.list_societies.return_value = [MagicMock()]
    mock_repo_cls.return_value = mock_repo
    
    service = SocietyService(mock_db)
    result = await service.list_societies()
    assert len(result) == 1


# --- Building Service Tests ---

@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_create_building_success(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_society.return_value = MagicMock()
    mock_building = MagicMock()
    mock_repo.create_building.return_value = mock_building
    mock_repo_cls.return_value = mock_repo
    
    service = BuildingService(mock_db)
    soc_id = uuid.uuid4()
    payload = BuildingCreate(name="Tower A")
    
    result = await service.create_building(soc_id, payload)
    mock_repo.get_society.assert_called_once_with(soc_id)
    mock_repo.create_building.assert_called_once_with(soc_id, payload)
    assert result == mock_building


@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_create_building_society_not_found(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_society.return_value = None
    mock_repo_cls.return_value = mock_repo
    
    service = BuildingService(mock_db)
    soc_id = uuid.uuid4()
    payload = BuildingCreate(name="Tower A")
    
    with pytest.raises(HTTPException) as exc:
        await service.create_building(soc_id, payload)
    assert exc.value.status_code == 404


# --- Floor Service Tests ---

@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_create_floor_success(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_building.return_value = MagicMock()
    mock_repo.get_floor_by_number.return_value = None
    mock_floor = MagicMock()
    mock_repo.create_floor.return_value = mock_floor
    mock_repo_cls.return_value = mock_repo
    
    service = FloorService(mock_db)
    b_id = uuid.uuid4()
    payload = FloorCreate(floor_number=1, floor_name="1st Floor")
    
    result = await service.create_floor(b_id, payload)
    mock_repo.get_building.assert_called_once_with(b_id)
    mock_repo.get_floor_by_number.assert_called_once_with(b_id, 1)
    mock_repo.create_floor.assert_called_once_with(b_id, payload)
    assert result == mock_floor


@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_create_floor_conflict(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_building.return_value = MagicMock()
    mock_repo.get_floor_by_number.return_value = MagicMock()
    mock_repo_cls.return_value = mock_repo
    
    service = FloorService(mock_db)
    b_id = uuid.uuid4()
    payload = FloorCreate(floor_number=1)
    
    with pytest.raises(HTTPException) as exc:
        await service.create_floor(b_id, payload)
    assert exc.value.status_code == 400


# --- Unit Service Tests ---

@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_create_unit_success(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_floor.return_value = MagicMock()
    mock_repo.get_unit_by_number.return_value = None
    mock_unit = MagicMock()
    mock_repo.create_unit.return_value = mock_unit
    mock_repo_cls.return_value = mock_repo
    
    service = UnitService(mock_db)
    f_id = uuid.uuid4()
    payload = UnitCreate(unit_number="101", unit_type=UnitType.FLAT, status=UnitStatus.VACANT)
    
    result = await service.create_unit(f_id, payload)
    mock_repo.get_floor.assert_called_once_with(f_id)
    mock_repo.get_unit_by_number.assert_called_once_with(f_id, "101")
    assert result == mock_unit


# --- Resident Service Tests ---

@pytest.mark.asyncio
@patch("app.societies.services.UserRepository")
@patch("app.societies.services.SocietyRepository")
async def test_assign_resident_success(mock_repo_cls, mock_user_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_user_repo = AsyncMock()
    
    mock_repo.get_unit.return_value = MagicMock()
    mock_user_repo.check_user_exist.return_value = MagicMock()
    mock_repo.get_resident_link.return_value = None
    mock_resident = MagicMock()
    mock_repo.assign_resident.return_value = mock_resident
    
    mock_repo_cls.return_value = mock_repo
    mock_user_repo_cls.return_value = mock_user_repo
    
    service = ResidentService(mock_db)
    u_id = uuid.uuid4()
    usr_id = uuid.uuid4()
    payload = ResidentAssign(user_id=usr_id, residency_type=ResidencyType.TENANT)
    
    result = await service.assign_resident(u_id, payload)
    assert result == mock_resident


# --- Vehicle Service Tests ---

@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_register_vehicle_success(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    
    mock_repo.get_unit.return_value = MagicMock()
    mock_repo.get_vehicle_by_reg_no.return_value = None
    mock_vehicle = MagicMock()
    mock_repo.register_vehicle.return_value = mock_vehicle
    mock_repo_cls.return_value = mock_repo
    
    service = VehicleService(mock_db)
    u_id = uuid.uuid4()
    payload = VehicleRegister(registration_number="ABC-1234", vehicle_type=VehicleType.CAR)
    
    result = await service.register_vehicle(u_id, payload)
    assert result == mock_vehicle


# --- Bulk Provisioning Service Tests ---

@pytest.mark.asyncio
@patch("app.societies.services.SocietyRepository")
async def test_provision_society_structure_success(mock_repo_cls):
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_society.return_value = MagicMock()
    mock_repo_cls.return_value = mock_repo
    
    service = BulkProvisionService(mock_db)
    soc_id = uuid.uuid4()
    payload = BulkProvisionRequest(
        buildings=[
            BuildingProvision(name="Tower A", number_of_floors=2, units_per_floor=3)
        ]
    )
    
    result = await service.provision_society_structure(soc_id, payload)
    assert len(result) == 1
    assert result[0].name == "Tower A"
