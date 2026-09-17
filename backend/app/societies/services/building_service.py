import uuid
from typing import List
from fastapi import HTTPException, status

from app.societies.models import BuildingModel
from app.societies.schemas import BuildingCreate, BuildingUpdate
from app.societies.services.base import BaseSocietyService


class BuildingService(BaseSocietyService):
    async def create_building(self, society_id: uuid.UUID, data: BuildingCreate) -> BuildingModel:
        society = await self.repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent society not found.",
            )
        return await self.repo.create_building(society_id, data)

    async def get_building(self, building_id: uuid.UUID) -> BuildingModel:
        building = await self.repo.get_building(building_id)
        if not building:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Building not found.",
            )
        return building

    async def list_buildings(self, society_id: uuid.UUID) -> List[BuildingModel]:
        return await self.repo.list_buildings(society_id)

    async def update_building(self, society_id: uuid.UUID, building_id: uuid.UUID, data: BuildingUpdate) -> BuildingModel:
        building = await self.get_building(building_id)
        if building.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Building does not belong to the specified society.",
            )
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(building, key, value)
        return building
