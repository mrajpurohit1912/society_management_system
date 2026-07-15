import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.societies.repository import SocietyRepository
from app.societies.schemas import (
    SocietyCreate,
    BuildingCreate,
    FloorCreate,
    UnitCreate,
    ResidentAssign,
    VehicleRegister
)
from app.societies.models import (
    SocietyModel,
    BuildingModel,
    FloorModel,
    UnitModel,
    UnitResidentModel,
    VehicleModel,
    UserSocietyRoleModel,
    UnitType,
    UnitStatus,
    ResidencyType,
    VehicleType,
    SocietyRole
)

@pytest.fixture
def mock_db_session():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def repo(mock_db_session):
    return SocietyRepository(mock_db_session)

# --- Society Repository Tests ---

@pytest.mark.asyncio
async def test_create_society(repo, mock_db_session):
    data = SocietyCreate(
        name="Sunshine Residency",
        registration_no="SR-101",
        address="1 Main St",
        city="Houston",
        state="TX",
        country="USA",
        zipcode="77001"
    )
    result = await repo.create_society(data)
    mock_db_session.add.assert_called_once()
    mock_db_session.flush.assert_called_once()
    assert result.name == "Sunshine Residency"
    assert result.registration_no == "SR-101"


@pytest.mark.asyncio
async def test_get_society(repo, mock_db_session):
    soc_id = uuid.uuid4()
    mock_society = SocietyModel(id=soc_id, name="Test Soc", registration_no="Reg-1", address="Addr", city="City", state="State", country="Country", zipcode="Zip")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_society
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_society(soc_id)
    mock_db_session.execute.assert_called_once()
    assert result == mock_society


@pytest.mark.asyncio
async def test_get_society_by_reg_no(repo, mock_db_session):
    mock_society = SocietyModel(name="Test Soc", registration_no="Reg-1", address="Addr", city="City", state="State", country="Country", zipcode="Zip")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_society
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_society_by_reg_no("Reg-1")
    assert result == mock_society


@pytest.mark.asyncio
async def test_list_societies(repo, mock_db_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [MagicMock()]
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.list_societies()
    assert len(result) == 1


# --- Building Repository Tests ---

@pytest.mark.asyncio
async def test_create_building(repo, mock_db_session):
    soc_id = uuid.uuid4()
    data = BuildingCreate(name="Tower A")
    result = await repo.create_building(soc_id, data)
    mock_db_session.add.assert_called_once()
    assert result.name == "Tower A"
    assert result.society_id == soc_id


@pytest.mark.asyncio
async def test_get_building(repo, mock_db_session):
    b_id = uuid.uuid4()
    mock_building = BuildingModel(id=b_id, name="Tower A")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_building
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_building(b_id)
    assert result == mock_building


@pytest.mark.asyncio
async def test_list_buildings(repo, mock_db_session):
    soc_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [MagicMock()]
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.list_buildings(soc_id)
    assert len(result) == 1


# --- Floor Repository Tests ---

@pytest.mark.asyncio
async def test_create_floor(repo, mock_db_session):
    b_id = uuid.uuid4()
    data = FloorCreate(floor_number=1, floor_name="1st Floor")
    result = await repo.create_floor(b_id, data)
    assert result.floor_number == 1
    assert result.building_id == b_id


@pytest.mark.asyncio
async def test_get_floor(repo, mock_db_session):
    f_id = uuid.uuid4()
    mock_floor = FloorModel(id=f_id, floor_number=1)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_floor
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_floor(f_id)
    assert result == mock_floor


@pytest.mark.asyncio
async def test_get_floor_by_number(repo, mock_db_session):
    b_id = uuid.uuid4()
    mock_floor = FloorModel(building_id=b_id, floor_number=2)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_floor
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_floor_by_number(b_id, 2)
    assert result == mock_floor


@pytest.mark.asyncio
async def test_list_floors(repo, mock_db_session):
    b_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [MagicMock()]
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.list_floors(b_id)
    assert len(result) == 1


# --- Unit Repository Tests ---

@pytest.mark.asyncio
async def test_create_unit(repo, mock_db_session):
    f_id = uuid.uuid4()
    data = UnitCreate(unit_number="101", unit_type=UnitType.FLAT, status=UnitStatus.VACANT)
    result = await repo.create_unit(f_id, data)
    assert result.unit_number == "101"
    assert result.floor_id == f_id


@pytest.mark.asyncio
async def test_get_unit(repo, mock_db_session):
    u_id = uuid.uuid4()
    mock_unit = UnitModel(id=u_id, unit_number="101")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_unit
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_unit(u_id)
    assert result == mock_unit


@pytest.mark.asyncio
async def test_get_unit_by_number(repo, mock_db_session):
    f_id = uuid.uuid4()
    mock_unit = UnitModel(floor_id=f_id, unit_number="102")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_unit
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_unit_by_number(f_id, "102")
    assert result == mock_unit


@pytest.mark.asyncio
async def test_list_units(repo, mock_db_session):
    f_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [MagicMock()]
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.list_units(f_id)
    assert len(result) == 1


# --- Resident Repository Tests ---

@pytest.mark.asyncio
async def test_assign_resident(repo, mock_db_session):
    u_id = uuid.uuid4()
    usr_id = uuid.uuid4()
    data = ResidentAssign(user_id=usr_id, residency_type=ResidencyType.TENANT)
    result = await repo.assign_resident(u_id, data)
    assert result.unit_id == u_id
    assert result.user_id == usr_id


@pytest.mark.asyncio
async def test_get_resident(repo, mock_db_session):
    res_id = uuid.uuid4()
    mock_resident = UnitResidentModel(id=res_id)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_resident
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_resident(res_id)
    assert result == mock_resident


@pytest.mark.asyncio
async def test_get_resident_link(repo, mock_db_session):
    u_id = uuid.uuid4()
    usr_id = uuid.uuid4()
    mock_resident = UnitResidentModel(unit_id=u_id, user_id=usr_id)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_resident
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_resident_link(u_id, usr_id)
    assert result == mock_resident


@pytest.mark.asyncio
async def test_list_residents(repo, mock_db_session):
    u_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [MagicMock()]
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.list_residents(u_id)
    assert len(result) == 1


# --- Vehicle Repository Tests ---

@pytest.mark.asyncio
async def test_register_vehicle(repo, mock_db_session):
    u_id = uuid.uuid4()
    res_id = uuid.uuid4()
    data = VehicleRegister(registration_number="ABC1234", vehicle_type=VehicleType.CAR, resident_id=res_id)
    result = await repo.register_vehicle(u_id, data)
    assert result.unit_id == u_id
    assert result.registration_number == "ABC1234"


@pytest.mark.asyncio
async def test_get_vehicle(repo, mock_db_session):
    v_id = uuid.uuid4()
    mock_vehicle = VehicleModel(id=v_id, registration_number="ABC1234")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_vehicle
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_vehicle(v_id)
    assert result == mock_vehicle


@pytest.mark.asyncio
async def test_get_vehicle_by_reg_no(repo, mock_db_session):
    mock_vehicle = VehicleModel(registration_number="ABC123")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_vehicle
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_vehicle_by_reg_no("abc123")
    assert result == mock_vehicle


@pytest.mark.asyncio
async def test_list_vehicles(repo, mock_db_session):
    u_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [MagicMock()]
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.list_vehicles(u_id)
    assert len(result) == 1


# --- User Society Role Repository Tests ---

@pytest.mark.asyncio
async def test_assign_user_society_role_new(repo, mock_db_session):
    s_id = uuid.uuid4()
    usr_id = uuid.uuid4()
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.assign_user_society_role(s_id, usr_id, "admin")
    assert result.role == "admin"
    assert result.society_id == s_id
    assert result.user_id == usr_id


@pytest.mark.asyncio
async def test_assign_user_society_role_existing(repo, mock_db_session):
    s_id = uuid.uuid4()
    usr_id = uuid.uuid4()
    existing_mapping = UserSocietyRoleModel(society_id=s_id, user_id=usr_id, role="member")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_mapping
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.assign_user_society_role(s_id, usr_id, "admin")
    assert result.role == "admin"


@pytest.mark.asyncio
async def test_get_user_society_role_model(repo, mock_db_session):
    s_id = uuid.uuid4()
    usr_id = uuid.uuid4()
    mock_role = UserSocietyRoleModel(society_id=s_id, user_id=usr_id, role="admin")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_role
    mock_db_session.execute.return_value = mock_result
    
    result = await repo.get_user_society_role_model(s_id, usr_id)
    assert result == mock_role
