import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
import structlog

from app.societies.repository import SocietyRepository
from app.authentication.repository import UserRepository
from app.core.email_service import EmailService
from app.authentication.models import UserModel
from app.societies.models import (
    SocietyModel,
    BuildingModel,
    FloorModel,
    UnitModel,
    UnitResidentModel,
    VehicleModel,
    UserSocietyRoleModel,
    MembershipStatus,
    SocietyRole
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

logger = structlog.get_logger(__name__)

class MembershipService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def request_membership(
        self, user_id: uuid.UUID, society_id: uuid.UUID, unit_id: Optional[uuid.UUID] = None, role: str = SocietyRole.RESIDENT.value
    ) -> UserSocietyRoleModel:
        # Verify society
        stmt_soc = select(SocietyModel).where(SocietyModel.id == society_id)
        res_soc = await self.db.execute(stmt_soc)
        society = res_soc.scalar_one_or_none()
        if not society:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found")

        # Verify unit if provided
        unit_number = None
        if unit_id:
            stmt_unit = select(UnitModel).where(UnitModel.id == unit_id)
            res_unit = await self.db.execute(stmt_unit)
            unit = res_unit.scalar_one_or_none()
            if not unit:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
            unit_number = unit.unit_number

        # Check existing membership
        stmt_mem = select(UserSocietyRoleModel).where(
            UserSocietyRoleModel.user_id == user_id,
            UserSocietyRoleModel.society_id == society_id,
        )
        res_mem = await self.db.execute(stmt_mem)
        existing = res_mem.scalar_one_or_none()

        if existing:
            if existing.status == MembershipStatus.APPROVED.value:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already an active member of this society")
            elif existing.status == MembershipStatus.PENDING.value:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your membership request for this society is already pending approval")
            else:
                existing.status = MembershipStatus.PENDING.value
                existing.unit_id = unit_id
                existing.role = role
                await self.db.flush()
                return existing

        membership = UserSocietyRoleModel(
            user_id=user_id,
            society_id=society_id,
            unit_id=unit_id,
            role=role,
            status=MembershipStatus.PENDING.value,
        )
        self.db.add(membership)
        await self.db.flush()

        logger.info("membership.requested", user_id=str(user_id), society_id=str(society_id), unit_id=str(unit_id) if unit_id else None)
        return membership

    async def get_user_memberships(self, user_id: uuid.UUID) -> List[UserSocietyRoleModel]:
        stmt = select(UserSocietyRoleModel).where(UserSocietyRoleModel.user_id == user_id)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def list_pending_requests(self, society_id: uuid.UUID) -> List[UserSocietyRoleModel]:
        stmt = select(UserSocietyRoleModel).where(
            UserSocietyRoleModel.society_id == society_id,
            UserSocietyRoleModel.status == MembershipStatus.PENDING.value
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def approve_membership(self, membership_id: uuid.UUID, approved_by_user_id: uuid.UUID) -> UserSocietyRoleModel:
        stmt = select(UserSocietyRoleModel).where(UserSocietyRoleModel.id == membership_id)
        res = await self.db.execute(stmt)
        membership = res.scalar_one_or_none()
        if not membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership request not found")

        membership.status = MembershipStatus.APPROVED.value
        membership.approved_by = approved_by_user_id
        await self.db.flush()

        # Fetch User & Society details for Email Notification
        stmt_user = select(UserModel).where(UserModel.user_id == membership.user_id)
        res_user = await self.db.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        stmt_soc = select(SocietyModel).where(SocietyModel.id == membership.society_id)
        res_soc = await self.db.execute(stmt_soc)
        society = res_soc.scalar_one_or_none()

        unit_number = "N/A"
        if membership.unit_id:
            stmt_u = select(UnitModel).where(UnitModel.id == membership.unit_id)
            res_u = await self.db.execute(stmt_u)
            unit_obj = res_u.scalar_one_or_none()
            if unit_obj:
                unit_number = unit_obj.unit_number

        # Fetch Email from Credentials
        if user and society:
            stmt_cred = select(UserRepository.get_user_credentials if hasattr(UserRepository, 'get_user_credentials') else UserModel)
            # Send notification email via Resend Service
            from app.authentication.models import AuthCredentialModel
            stmt_c = select(AuthCredentialModel).where(AuthCredentialModel.user_id == user.user_id)
            res_c = await self.db.execute(stmt_c)
            cred = res_c.scalar_one_or_none()
            if cred:
                EmailService.send_membership_approval_email(
                    to_email=cred.identifier,
                    name=f"{user.first_name} {user.last_name}",
                    society_name=society.name,
                    unit_number=unit_number
                )

        logger.info("membership.approved", membership_id=str(membership_id), user_id=str(membership.user_id))
        return membership

    async def reject_membership(self, membership_id: uuid.UUID, approved_by_user_id: uuid.UUID, reason: Optional[str] = None) -> UserSocietyRoleModel:
        stmt = select(UserSocietyRoleModel).where(UserSocietyRoleModel.id == membership_id)
        res = await self.db.execute(stmt)
        membership = res.scalar_one_or_none()
        if not membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership request not found")

        membership.status = MembershipStatus.REJECTED.value
        membership.approved_by = approved_by_user_id
        await self.db.flush()

        stmt_user = select(UserModel).where(UserModel.user_id == membership.user_id)
        res_user = await self.db.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        stmt_soc = select(SocietyModel).where(SocietyModel.id == membership.society_id)
        res_soc = await self.db.execute(stmt_soc)
        society = res_soc.scalar_one_or_none()

        if user and society:
            from app.authentication.models import AuthCredentialModel
            stmt_c = select(AuthCredentialModel).where(AuthCredentialModel.user_id == user.user_id)
            res_c = await self.db.execute(stmt_c)
            cred = res_c.scalar_one_or_none()
            if cred:
                EmailService.send_membership_rejection_email(
                    to_email=cred.identifier,
                    name=f"{user.first_name} {user.last_name}",
                    society_name=society.name,
                    reason=reason
                )

        logger.info("membership.rejected", membership_id=str(membership_id), user_id=str(membership.user_id))
        return membership


class SocietyService:
    def __init__(self, db: AsyncSession):
        self.repo = SocietyRepository(db)

    async def create_society(self, data: SocietyCreate) -> SocietyModel:
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
        building = await self.repo.get_building(building_id)
        if not building:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent building not found."
            )
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
        floor = await self.repo.get_floor(floor_id)
        if not floor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent floor not found."
            )
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
        unit = await self.repo.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found."
            )
            
        user = await self.user_repo.check_user_exist(data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
            
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
        unit = await self.repo.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found."
            )
            
        existing = await self.repo.get_vehicle_by_reg_no(data.registration_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle with registration number '{data.registration_number}' is already registered."
            )
            
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
        society = await self.repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Society not found."
            )
            
        buildings_created = []
        for b_data in data.buildings:
            building = BuildingModel(
                society_id=society_id,
                name=b_data.name
            )
            self.db.add(building)
            await self.db.flush()
            
            for floor_no in range(0, b_data.number_of_floors + 1):
                floor_name = "Ground Floor" if floor_no == 0 else f"Floor {floor_no}"
                floor = FloorModel(
                    building_id=building.id,
                    floor_number=floor_no,
                    floor_name=floor_name
                )
                self.db.add(floor)
                await self.db.flush()
                
                for unit_idx in range(1, b_data.units_per_floor + 1):
                    unit_number = f"{floor_no}{unit_idx:02d}"
                    unit = UnitModel(
                        floor_id=floor.id,
                        unit_number=unit_number
                    )
                    self.db.add(unit)
            
            buildings_created.append(building)
            
        await self.db.flush()
        return buildings_created
