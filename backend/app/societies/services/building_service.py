import uuid
from typing import List
from fastapi import HTTPException, status

from app.societies.models import BuildingModel, SocietyStatus
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

        existing_buildings = await self.repo.list_buildings(society_id)     
        normalized_name = data.name.strip().lower()
        if any(b.name.strip().lower() == normalized_name for b in existing_buildings):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Building with name '{data.name}' already exists in the society.",
            )
        
        building = await self.repo.create_building(society_id, data)
        if society.status == SocietyStatus.PENDING_SETUP.value:
            society.status = SocietyStatus.ACTIVE.value
            await self.db.flush()

        return building

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

    async def delete_building(self, society_id: uuid.UUID, building_id: uuid.UUID) -> None:
        building = await self.get_building(building_id)
        if building.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Building does not belong to the specified society.",
            )
        await self.repo.delete_building(building)
