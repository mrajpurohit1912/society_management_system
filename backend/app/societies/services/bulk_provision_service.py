import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.societies.models import BuildingModel, FloorModel, UnitModel
from app.societies.schemas import BulkProvisionRequest
from app.societies import services as services_pkg


class BulkProvisionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = services_pkg.SocietyRepository(db)

    async def provision_society_structure(
        self, society_id: uuid.UUID, data: BulkProvisionRequest
    ) -> List[BuildingModel]:
        society = await self.repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Society not found.",
            )

        buildings_created = []
        for b_data in data.buildings:
            building = BuildingModel(
                society_id=society_id,
                name=b_data.name,
            )
            self.db.add(building)
            await self.db.flush()

            for floor_no in range(0, b_data.number_of_floors + 1):
                floor_name = "Ground Floor" if floor_no == 0 else f"Floor {floor_no}"
                floor = FloorModel(
                    building_id=building.id,
                    floor_number=floor_no,
                    floor_name=floor_name,
                )
                self.db.add(floor)
                await self.db.flush()

                for unit_idx in range(1, b_data.units_per_floor + 1):
                    unit_number = f"{floor_no}{unit_idx:02d}"
                    unit = UnitModel(
                        floor_id=floor.id,
                        unit_number=unit_number,
                    )
                    self.db.add(unit)

            buildings_created.append(building)

        await self.db.flush()
        return buildings_created
