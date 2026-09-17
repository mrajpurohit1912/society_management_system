import uuid
from typing import List
from fastapi import HTTPException, status

from app.societies.models import VehicleModel
from app.societies.schemas import VehicleRegister
from app.societies.services.base import BaseSocietyService


class VehicleService(BaseSocietyService):
    async def register_vehicle(self, unit_id: uuid.UUID, data: VehicleRegister) -> VehicleModel:
        unit = await self.repo.get_unit(unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found.",
            )

        existing = await self.repo.get_vehicle_by_reg_no(data.registration_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle with registration number '{data.registration_number}' is already registered.",
            )

        if data.resident_id:
            resident = await self.repo.get_resident(data.resident_id)
            if not resident:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resident not found.",
                )

        return await self.repo.register_vehicle(unit_id, data)

    async def get_vehicle(self, vehicle_id: uuid.UUID) -> VehicleModel:
        vehicle = await self.repo.get_vehicle(vehicle_id)
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found.",
            )
        return vehicle

    async def list_vehicles(self, unit_id: uuid.UUID) -> List[VehicleModel]:
        return await self.repo.list_vehicles(unit_id)
