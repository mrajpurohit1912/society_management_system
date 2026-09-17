import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.societies.models import UnitResidentModel
from app.societies.schemas import ResidentAssign
from app.societies import services as services_pkg


class ResidentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = services_pkg.SocietyRepository(db)
        self.user_repo = services_pkg.UserRepository(db)

    async def assign_resident(self, unit_id: uuid.UUID, data: ResidentAssign) -> UnitResidentModel:
        unit = await self.repo.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found.",
            )

        user = await self.user_repo.check_user_exist(data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        existing = await self.repo.get_resident_link(unit_id, data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user is already linked to this unit.",
            )

        return await self.repo.assign_resident(unit_id, data)

    async def get_resident(self, resident_id: uuid.UUID) -> UnitResidentModel:
        resident = await self.repo.get_resident(resident_id)
        if not resident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resident assignment not found.",
            )
        return resident

    async def list_residents(self, unit_id: uuid.UUID) -> List[UnitResidentModel]:
        return await self.repo.list_residents(unit_id)
