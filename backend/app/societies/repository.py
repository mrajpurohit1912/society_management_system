import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.societies.models import (
    SocietyModel,
    BuildingModel,
    FloorModel,
    UnitModel,
    UnitResidentModel,
    VehicleModel,
    UserSocietyRoleModel,
    SocietyRole
)

class SocietyRepository:
    """
    Data Access Layer (Repository Pattern) for Society Management.
    Encapsulates all database operations using SQLAlchemy 2.0 Async Session.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Society Operations ---
    async def create_society(self, data) -> SocietyModel:
        society = SocietyModel(
            name=data.name,
            registration_no=data.registration_no,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            zipcode=data.zipcode,
            email=data.email,
            phone=data.phone
        )
        self.db.add(society)
        await self.db.flush()
        return society

    async def get_society(self, society_id: uuid.UUID) -> Optional[SocietyModel]:
        query = select(SocietyModel).where(SocietyModel.id == society_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_society_by_reg_no(self, registration_no: str) -> Optional[SocietyModel]:
        query = select(SocietyModel).where(SocietyModel.registration_no == registration_no)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_societies(self) -> List[SocietyModel]:
        query = select(SocietyModel).order_by(SocietyModel.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Building Operations ---
    async def create_building(self, society_id: uuid.UUID, data) -> BuildingModel:
        building = BuildingModel(
            society_id=society_id,
            name=data.name
        )
        self.db.add(building)
        await self.db.flush()
        return building

    async def get_building(self, building_id: uuid.UUID) -> Optional[BuildingModel]:
        query = select(BuildingModel).where(BuildingModel.id == building_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_buildings(self, society_id: uuid.UUID) -> List[BuildingModel]:
        query = select(BuildingModel).where(BuildingModel.society_id == society_id).order_by(BuildingModel.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Floor Operations ---
    async def create_floor(self, building_id: uuid.UUID, data) -> FloorModel:
        floor = FloorModel(
            building_id=building_id,
            floor_number=data.floor_number,
            floor_name=data.floor_name
        )
        self.db.add(floor)
        await self.db.flush()
        return floor

    async def get_floor(self, floor_id: uuid.UUID) -> Optional[FloorModel]:
        query = select(FloorModel).where(FloorModel.id == floor_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_floor_by_number(self, building_id: uuid.UUID, floor_number: int) -> Optional[FloorModel]:
        query = select(FloorModel).where(
            FloorModel.building_id == building_id,
            FloorModel.floor_number == floor_number
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_floors(self, building_id: uuid.UUID) -> List[FloorModel]:
        query = select(FloorModel).where(FloorModel.building_id == building_id).order_by(FloorModel.floor_number)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Unit/Flat Operations ---
    async def create_unit(self, floor_id: uuid.UUID, data) -> UnitModel:
        unit = UnitModel(
            floor_id=floor_id,
            unit_number=data.unit_number,
            unit_type=data.unit_type.value if hasattr(data.unit_type, 'value') else data.unit_type,
            status=data.status.value if hasattr(data.status, 'value') else data.status
        )
        self.db.add(unit)
        await self.db.flush()
        return unit

    async def get_unit(self, unit_id: uuid.UUID) -> Optional[UnitModel]:
        query = select(UnitModel).where(UnitModel.id == unit_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_unit_by_number(self, floor_id: uuid.UUID, unit_number: str) -> Optional[UnitModel]:
        query = select(UnitModel).where(
            UnitModel.floor_id == floor_id,
            UnitModel.unit_number == unit_number
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_units(self, floor_id: uuid.UUID) -> List[UnitModel]:
        query = select(UnitModel).where(UnitModel.floor_id == floor_id).order_by(UnitModel.unit_number)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Resident Operations ---
    async def assign_resident(self, unit_id: uuid.UUID, data) -> UnitResidentModel:
        resident = UnitResidentModel(
            unit_id=unit_id,
            user_id=data.user_id,
            residency_type=data.residency_type.value if hasattr(data.residency_type, 'value') else data.residency_type,
            is_primary_contact=data.is_primary_contact,
            start_date=data.start_date or datetime.now(),
            end_date=data.end_date
        )
        self.db.add(resident)
        await self.db.flush()
        return resident

    async def get_resident(self, resident_id: uuid.UUID) -> Optional[UnitResidentModel]:
        query = select(UnitResidentModel).where(UnitResidentModel.id == resident_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_resident_link(self, unit_id: uuid.UUID, user_id: uuid.UUID) -> Optional[UnitResidentModel]:
        query = select(UnitResidentModel).where(
            UnitResidentModel.unit_id == unit_id,
            UnitResidentModel.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_residents(self, unit_id: uuid.UUID) -> List[UnitResidentModel]:
        query = select(UnitResidentModel).where(UnitResidentModel.unit_id == unit_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Vehicle Operations ---
    async def register_vehicle(self, unit_id: uuid.UUID, data) -> VehicleModel:
        vehicle = VehicleModel(
            unit_id=unit_id,
            resident_id=data.resident_id,
            vehicle_type=data.vehicle_type.value if hasattr(data.vehicle_type, 'value') else data.vehicle_type,
            registration_number=data.registration_number.upper().strip()
        )
        self.db.add(vehicle)
        await self.db.flush()
        return vehicle

    async def get_vehicle(self, vehicle_id: uuid.UUID) -> Optional[VehicleModel]:
        query = select(VehicleModel).where(VehicleModel.id == vehicle_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_vehicle_by_reg_no(self, registration_number: str) -> Optional[VehicleModel]:
        query = select(VehicleModel).where(
            VehicleModel.registration_number == registration_number.upper().strip()
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_vehicles(self, unit_id: uuid.UUID) -> List[VehicleModel]:
        query = select(VehicleModel).where(VehicleModel.unit_id == unit_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Scoped Roles (RBAC) Operations ---
    async def assign_user_society_role(self, society_id: uuid.UUID, user_id: uuid.UUID, role: str) -> UserSocietyRoleModel:
        # Check if mapping already exists
        query = select(UserSocietyRoleModel).where(
            UserSocietyRoleModel.user_id == user_id,
            UserSocietyRoleModel.society_id == society_id
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.role = role
            await self.db.flush()
            return existing

        user_role = UserSocietyRoleModel(
            user_id=user_id,
            society_id=society_id,
            role=role
        )
        self.db.add(user_role)
        await self.db.flush()
        return user_role

    async def get_user_society_role(self, society_id: uuid.UUID, user_id: uuid.UUID) -> Optional[str]:
        query = select(UserSocietyRoleModel.role).where(
            UserSocietyRoleModel.user_id == user_id,
            UserSocietyRoleModel.society_id == society_id
        )
        result = await self.db.execute(query)
        return result.scalar_one() if result.raw else None # type: ignore
        
    async def get_user_society_role_model(self, society_id: uuid.UUID, user_id: uuid.UUID) -> Optional[UserSocietyRoleModel]:
        query = select(UserSocietyRoleModel).where(
            UserSocietyRoleModel.user_id == user_id,
            UserSocietyRoleModel.society_id == society_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
