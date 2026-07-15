import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.societies.repository import SocietyRepository
from app.authentication.repository import UserRepository
from app.societies.models import (
    SocietyModel,
    BuildingModel,
    FloorModel,
    UnitModel,
    UnitResidentModel,
    VehicleModel,
    UserSocietyRoleModel
)
from app.societies.schemas import (
    SocietyCreate,
    SocietyUpdate,
    BuildingCreate,
    BuildingUpdate,
    FloorCreate,
    UnitCreate,
    UnitUpdate,
    ResidentAssign,
    VehicleRegister,
    BulkProvisionRequest
)

class SocietyService:
    def __init__(self, db: AsyncSession):
        self.repo = SocietyRepository(db)

    async def create_society(self, data: SocietyCreate) -> SocietyModel:
        # Check registration number uniqueness
        existing = await self.repo.get_society_by_reg_no(data.registration_no)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Society with registration number '{data.registration_no}' already exists."
            )
        return await self.repo.create_society(data)

    async def get_society(self, society_id: uuid.UUID) -> SocietyModel:
        society = await self.repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Society not found."
            )
        return society

    async def list_societies(self) -> List[SocietyModel]:
        return await self.repo.list_societies()

    async def update_society(self, society_id: uuid.UUID, data: SocietyUpdate) -> SocietyModel:
        society = await self.get_society(society_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(society, key, value)
        return society



class BuildingService:
    def __init__(self, db: AsyncSession):
        self.repo = SocietyRepository(db)

    async def create_building(self, society_id: uuid.UUID, data: BuildingCreate) -> BuildingModel:
        # Verify society exists
        society = await self.repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent society not found."
            )
        return await self.repo.create_building(society_id, data)

    async def get_building(self, building_id: uuid.UUID) -> BuildingModel:
        building = await self.repo.get_building(building_id)
        if not building:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Building not found."
            )
        return building

    async def list_buildings(self, society_id: uuid.UUID) -> List[BuildingModel]:
        return await self.repo.list_buildings(society_id)

    async def update_building(self, society_id: uuid.UUID, building_id: uuid.UUID, data: BuildingUpdate) -> BuildingModel:
        building = await self.get_building(building_id)
        if building.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Building does not belong to the specified society."
            )
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(building, key, value)
        return building



class FloorService:
    def __init__(self, db: AsyncSession):
        self.repo = SocietyRepository(db)

    async def create_floor(self, building_id: uuid.UUID, data: FloorCreate) -> FloorModel:
        # Verify building exists
        building = await self.repo.get_building(building_id)
        if not building:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent building not found."
            )
        # Verify floor number is unique in this building
        existing = await self.repo.get_floor_by_number(building_id, data.floor_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Floor number {data.floor_number} already exists in this building."
            )
        return await self.repo.create_floor(building_id, data)

    async def get_floor(self, floor_id: uuid.UUID) -> FloorModel:
        floor = await self.repo.get_floor(floor_id)
        if not floor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Floor not found."
            )
        return floor

    async def list_floors(self, building_id: uuid.UUID) -> List[FloorModel]:
        return await self.repo.list_floors(building_id)


class UnitService:
    def __init__(self, db: AsyncSession):
        self.repo = SocietyRepository(db)

    async def create_unit(self, floor_id: uuid.UUID, data: UnitCreate) -> UnitModel:
        # Verify floor exists
        floor = await self.repo.get_floor(floor_id)
        if not floor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent floor not found."
            )
        # Verify unit number is unique on this floor
        existing = await self.repo.get_unit_by_number(floor_id, data.unit_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unit '{data.unit_number}' already exists on this floor."
            )
        return await self.repo.create_unit(floor_id, data)

    async def get_unit(self, unit_id: uuid.UUID) -> UnitModel:
        unit = await self.repo.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found."
            )
        return unit

    async def list_units(self, floor_id: uuid.UUID) -> List[UnitModel]:
        return await self.repo.list_units(floor_id)

    async def update_unit(self, floor_id: uuid.UUID, unit_id: uuid.UUID, data: UnitUpdate) -> UnitModel:
        unit = await self.get_unit(unit_id)
        if unit.floor_id != floor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unit does not belong to the specified floor."
            )
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(unit, key, value)
        return unit



class ResidentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SocietyRepository(db)
        self.user_repo = UserRepository(db)

    async def assign_resident(self, unit_id: uuid.UUID, data: ResidentAssign) -> UnitResidentModel:
        # Verify unit exists
        unit = await self.repo.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_444_NOT_FOUND if hasattr(status, 'HTTP_444_NOT_FOUND') else 404,
                detail="Unit not found."
            )
            
        # Verify user exists
        user = await self.user_repo.check_user_exist(data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
            
        # Check if already assigned
        existing = await self.repo.get_resident_link(unit_id, data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user is already linked to this unit."
            )
            
        return await self.repo.assign_resident(unit_id, data)

    async def get_resident(self, resident_id: uuid.UUID) -> UnitResidentModel:
        resident = await self.repo.get_resident(resident_id)
        if not resident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resident assignment not found."
            )
        return resident

    async def list_residents(self, unit_id: uuid.UUID) -> List[UnitResidentModel]:
        return await self.repo.list_residents(unit_id)


class VehicleService:
    def __init__(self, db: AsyncSession):
        self.repo = SocietyRepository(db)

    async def register_vehicle(self, unit_id: uuid.UUID, data: VehicleRegister) -> VehicleModel:
        # Verify unit exists
        unit = await self.repo.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found."
            )
            
        # Verify registration number is unique
        existing = await self.repo.get_vehicle_by_reg_no(data.registration_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle with registration number '{data.registration_number}' is already registered."
            )
            
        # Verify resident exists if provided
        if data.resident_id:
            resident = await self.repo.get_resident(data.resident_id)
            if not resident:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resident not found."
                )
                
        return await self.repo.register_vehicle(unit_id, data)

    async def get_vehicle(self, vehicle_id: uuid.UUID) -> VehicleModel:
        vehicle = await self.repo.get_vehicle(vehicle_id)
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found."
            )
        return vehicle

    async def list_vehicles(self, unit_id: uuid.UUID) -> List[VehicleModel]:
        return await self.repo.list_vehicles(unit_id)


class BulkProvisionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SocietyRepository(db)

    async def provision_society_structure(self, society_id: uuid.UUID, data: BulkProvisionRequest) -> List[BuildingModel]:
        # Verify society exists
        society = await self.repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Society not found."
            )
            
        buildings_created = []
        
        # Note: We rely on the caller wrapping this call in a transaction block
        # (e.g. `async with db.begin()`) or we can manage it here.
        for b_data in data.buildings:
            # 1. Create Building
            building = BuildingModel(
                society_id=society_id,
                name=b_data.name
            )
            self.db.add(building)
            await self.db.flush()
            
            # 2. Create Floors (starting from 0 for Ground Floor)
            for floor_no in range(0, b_data.number_of_floors + 1):
                floor_name = "Ground Floor" if floor_no == 0 else f"Floor {floor_no}"
                floor = FloorModel(
                    building_id=building.id,
                    floor_number=floor_no,
                    floor_name=floor_name
                )
                self.db.add(floor)
                await self.db.flush()
                
                # 3. Create Units for this Floor
                for unit_idx in range(1, b_data.units_per_floor + 1):
                    # Format: Floor Number + 2 digit Unit index (e.g. 001, 101, 201)
                    unit_number = f"{floor_no}{unit_idx:02d}"
                    unit = UnitModel(
                        floor_id=floor.id,
                        unit_number=unit_number
                    )
                    self.db.add(unit)
            
            buildings_created.append(building)
            
        await self.db.flush()
        return buildings_created
