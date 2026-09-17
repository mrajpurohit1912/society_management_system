import uuid
from typing import List
from fastapi import HTTPException, status

from app.societies.models import SocietyModel
from app.societies.schemas import SocietyCreate, SocietyUpdate
from app.societies.services.base import BaseSocietyService


class SocietyService(BaseSocietyService):
    async def create_society(self, data: SocietyCreate) -> SocietyModel:
        existing = await self.repo.get_society_by_reg_no(data.registration_no)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Society with registration number '{data.registration_no}' already exists.",
            )
        return await self.repo.create_society(data)

    async def get_society(self, society_id: uuid.UUID) -> SocietyModel:
        society = await self.repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Society not found.",
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
