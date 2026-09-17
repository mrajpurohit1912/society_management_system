import uuid
from typing import List
from fastapi import HTTPException, status

from app.societies.models import UnitModel
from app.societies.schemas import UnitCreate, UnitUpdate
from app.societies.services.base import BaseSocietyService


class UnitService(BaseSocietyService):
    async def create_unit(self, floor_id: uuid.UUID, data: UnitCreate) -> UnitModel:
        floor = await self.repo.get_floor(floor_id)
        if not floor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent floor not found.",
            )
        existing = await self.repo.get_unit_by_number(floor_id, data.unit_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unit '{data.unit_number}' already exists on this floor.",
            )
        return await self.repo.create_unit(floor_id, data)

    async def get_unit(self, unit_id: uuid.UUID) -> UnitModel:
        unit = await self.repo.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found.",
            )
        return unit

    async def list_units(self, floor_id: uuid.UUID) -> List[UnitModel]:
        return await self.repo.list_units(floor_id)

    async def update_unit(self, floor_id: uuid.UUID, unit_id: uuid.UUID, data: UnitUpdate) -> UnitModel:
        unit = await self.get_unit(unit_id)
        if unit.floor_id != floor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unit does not belong to the specified floor.",
            )
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(unit, key, value)
        return unit
