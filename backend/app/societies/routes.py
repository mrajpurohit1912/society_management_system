import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_platform_admin, require_society_admin
from app.authentication.models import UserModel
from app.societies.schemas import (
    SocietyCreate,
    SocietyResponse,
    BuildingCreate,
    BuildingResponse,
    FloorCreate,
    FloorResponse,
    UnitCreate,
    UnitResponse,
    ResidentAssign,
    ResidentResponse,
    VehicleRegister,
    VehicleResponse,
    UserSocietyRoleAssign,
    UserSocietyRoleResponse,
    BulkProvisionRequest
)
from app.societies.services import (
    SocietyService,
    BuildingService,
    FloorService,
    UnitService,
    ResidentService,
    VehicleService,
    BulkProvisionService
)

router = APIRouter(prefix="/societies", tags=["Society Management"])


# --- Society Endpoints ---

@router.post("", response_model=SocietyResponse, status_code=status.HTTP_201_CREATED)
async def create_society(
    payload: SocietyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_platform_admin)
):
    """
    Create a new housing society. Restricted to Platform/Super Admins.
    """
    service = SocietyService(db)
    # Perform inside transaction block
    async with db.begin():
        return await service.create_society(payload)


@router.get("", response_model=List[SocietyResponse])
async def list_societies(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    List all housing societies registered on the platform.
    """
    service = SocietyService(db)
    return await service.list_societies()


@router.get("/{society_id}", response_model=SocietyResponse)
async def get_society(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get details of a specific housing society by its ID.
    """
    service = SocietyService(db)
    return await service.get_society(society_id)


# --- Scoped RBAC Endpoints ---

@router.post("/{society_id}/assign-role", response_model=UserSocietyRoleResponse, status_code=status.HTTP_200_OK)
async def assign_user_society_role(
    society_id: uuid.UUID,
    payload: UserSocietyRoleAssign,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    """
    Assign a role (admin, member, security) to a user within a specific society.
    Restricted to Society Admins.
    """
    service = SocietyService(db)
    async with db.begin():
        user_role = await service.repo.assign_user_society_role(
            society_id=society_id,
            user_id=payload.user_id,
            role=payload.role.value
        )
        return user_role


# --- Building Endpoints ---

@router.post("/{society_id}/buildings", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(
    society_id: uuid.UUID,
    payload: BuildingCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    """
    Create a new building/wing inside a society. Restricted to Society Admins.
    """
    service = BuildingService(db)
    async with db.begin():
        return await service.create_building(society_id, payload)


@router.get("/{society_id}/buildings", response_model=List[BuildingResponse])
async def list_buildings(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    List all buildings/wings in a specific society.
    """
    service = BuildingService(db)
    return await service.list_buildings(society_id)


# --- Floor Endpoints ---

@router.post("/{society_id}/buildings/{building_id}/floors", response_model=FloorResponse, status_code=status.HTTP_201_CREATED)
async def create_floor(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: FloorCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    """
    Create a floor inside a building. Restricted to Society Admins.
    """
    # Double check that building belongs to society
    b_service = BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society."
        )

    service = FloorService(db)
    async with db.begin():
        return await service.create_floor(building_id, payload)


@router.get("/{society_id}/buildings/{building_id}/floors", response_model=List[FloorResponse])
async def list_floors(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    List all floors in a building.
    """
    b_service = BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society."
        )

    service = FloorService(db)
    return await service.list_floors(building_id)


# --- Unit Endpoints ---

@router.post("/{society_id}/buildings/{building_id}/floors/{floor_id}/units", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
async def create_unit(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    payload: UnitCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    """
    Create a new unit/flat on a floor. Restricted to Society Admins.
    """
    # Validate hierarchy
    f_service = FloorService(db)
    floor = await f_service.get_floor(floor_id)
    if floor.building_id != building_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Floor does not belong to the specified building."
        )

    b_service = BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society."
        )

    service = UnitService(db)
    async with db.begin():
        return await service.create_unit(floor_id, payload)


@router.get("/{society_id}/buildings/{building_id}/floors/{floor_id}/units", response_model=List[UnitResponse])
async def list_units(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    List all units/flats on a floor.
    """
    f_service = FloorService(db)
    floor = await f_service.get_floor(floor_id)
    if floor.building_id != building_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Floor does not belong to the specified building."
        )

    b_service = BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society."
        )

    service = UnitService(db)
    return await service.list_units(floor_id)


# --- Resident Endpoints ---

@router.post("/{society_id}/units/{unit_id}/residents", response_model=ResidentResponse, status_code=status.HTTP_201_CREATED)
async def assign_resident(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    payload: ResidentAssign,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    """
    Assign a user as a resident to a unit. Restricted to Society Admins.
    """
    # Verify unit belongs to the society
    u_service = UnitService(db)
    unit = await u_service.get_unit(unit_id)
    f_service = FloorService(db)
    floor = await f_service.get_floor(unit.floor_id)
    b_service = BuildingService(db)
    building = await b_service.get_building(floor.building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit does not belong to the specified society."
        )

    service = ResidentService(db)
    async with db.begin():
        return await service.assign_resident(unit_id, payload)


@router.get("/{society_id}/units/{unit_id}/residents", response_model=List[ResidentResponse])
async def list_residents(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    List all residents assigned to a unit.
    """
    u_service = UnitService(db)
    unit = await u_service.get_unit(unit_id)
    f_service = FloorService(db)
    floor = await f_service.get_floor(unit.floor_id)
    b_service = BuildingService(db)
    building = await b_service.get_building(floor.building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit does not belong to the specified society."
        )

    service = ResidentService(db)
    return await service.list_residents(unit_id)


# --- Vehicle Endpoints ---

@router.post("/{society_id}/units/{unit_id}/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def register_vehicle(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    payload: VehicleRegister,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Register a vehicle to a unit. Open to logged-in members (a resident registers their own car) or admins.
    """
    # Verify unit belongs to the society
    u_service = UnitService(db)
    unit = await u_service.get_unit(unit_id)
    f_service = FloorService(db)
    floor = await f_service.get_floor(unit.floor_id)
    b_service = BuildingService(db)
    building = await b_service.get_building(floor.building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit does not belong to the specified society."
        )

    service = VehicleService(db)
    async with db.begin():
        return await service.register_vehicle(unit_id, payload)


@router.get("/{society_id}/units/{unit_id}/vehicles", response_model=List[VehicleResponse])
async def list_vehicles(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    List all registered vehicles for a unit.
    """
    u_service = UnitService(db)
    unit = await u_service.get_unit(unit_id)
    f_service = FloorService(db)
    floor = await f_service.get_floor(unit.floor_id)
    b_service = BuildingService(db)
    building = await b_service.get_building(floor.building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit does not belong to the specified society."
        )

    service = VehicleService(db)
    return await service.list_vehicles(unit_id)


# --- Bulk Provisioning Endpoints ---

@router.post("/{society_id}/provision", response_model=List[BuildingResponse], status_code=status.HTTP_201_CREATED)
async def provision_society_structure(
    society_id: uuid.UUID,
    payload: BulkProvisionRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    """
    Bulk provision buildings, floors, and units for a society in a single atomic database transaction.
    Restricted to Society Admins.
    """
    service = BulkProvisionService(db)
    async with db.begin():
        return await service.provision_society_structure(society_id, payload)
