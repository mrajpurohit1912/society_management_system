import uuid
from typing import List
from fastapi import HTTPException, status

from app.societies.models import FloorModel
from app.societies.schemas import FloorCreate
from app.societies.services.base import BaseSocietyService


class FloorService(BaseSocietyService):
    async def create_floor(self, building_id: uuid.UUID, data: FloorCreate) -> FloorModel:
        building = await self.repo.get_building(building_id)
        if not building:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent building not found.",
            )
        existing = await self.repo.get_floor_by_number(building_id, data.floor_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Floor number {data.floor_number} already exists in this building.",
            )
        return await self.repo.create_floor(building_id, data)

    async def get_floor(self, floor_id: uuid.UUID) -> FloorModel:
        floor = await self.repo.get_floor(floor_id)
        if not floor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Floor not found.",
            )
        return floor

    async def list_floors(self, building_id: uuid.UUID) -> List[FloorModel]:
        return await self.repo.list_floors(building_id)
