import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.societies.models import BuildingModel, FloorModel, UnitModel, SocietyStatus
from app.societies.schemas import BulkProvisionRequest, BuildingPopulateRequest
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
        
        # 1. Load existing building names in this society                                                                                                                        
        existing_buildings = await self.repo.list_buildings(society_id)                                                                                                          
        existing_names = {b.name.strip().lower() for b in existing_buildings}       


        seen_in_payload = set()
        for b_data in data.buildings:
            normalized_name = b_data.name.strip().lower()

            # Check against database
            if normalized_name in existing_names:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Building with name '{b_data.name.strip()}' already exists in this society.",
                )

            # Check against duplicate in same payload
            if normalized_name in seen_in_payload:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Duplicate building name '{b_data.name.strip()}' found in the request.",
                )
            seen_in_payload.add(normalized_name)

        buildings_created = []
        for b_data in data.buildings:


            building = BuildingModel(
                society_id=society_id,
                name=b_data.name,
            )
            self.db.add(building)
            await self.db.flush()

            # Build quick-lookup map for any custom floor overrides
            custom_map = {cf.floor_number: cf for cf in (b_data.custom_floors or [])}

            for floor_no in range(0, b_data.number_of_floors + 1):
                override = custom_map.get(floor_no)

                # 1. Floor Name (override or default)
                default_name = "Ground Floor" if floor_no == 0 else f"Floor {floor_no}"
                floor_name = override.floor_name if (override and override.floor_name) else default_name

                floor = FloorModel(
                    building_id=building.id,
                    floor_number=floor_no,
                    floor_name=floor_name,
                )
                self.db.add(floor)
                await self.db.flush()

                # 2. Units count (override or default)
                unit_count = override.units_count if override is not None else b_data.units_per_floor
                prefix = override.unit_prefix.strip() if (override and override.unit_prefix) else ""

                for unit_idx in range(1, unit_count + 1):
                    if prefix:
                        unit_number = f"{prefix}-{floor_no}{unit_idx:02d}" if not prefix.endswith("-") else f"{prefix}{floor_no}{unit_idx:02d}"
                    else:
                        unit_number = f"{floor_no}{unit_idx:02d}"

                    unit = UnitModel(
                        floor_id=floor.id,
                        unit_number=unit_number,
                    )
                    self.db.add(unit)

            buildings_created.append(building)

        if society.status == SocietyStatus.PENDING_SETUP.value:
            society.status = SocietyStatus.ACTIVE.value

        await self.db.flush()
        return buildings_created

    async def populate_existing_building(
        self, society_id: uuid.UUID, building_id: uuid.UUID, data: BuildingPopulateRequest
    ) -> BuildingModel:
        building = await self.repo.get_building(building_id)
        if not building or building.society_id != society_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Building not found in this society.",
            )

        custom_map = {cf.floor_number: cf for cf in (data.custom_floors or [])}

        for floor_no in range(0, data.number_of_floors + 1):
            override = custom_map.get(floor_no)

            default_name = "Ground Floor" if floor_no == 0 else f"Floor {floor_no}"
            floor_name = override.floor_name if (override and override.floor_name) else default_name

            floor = FloorModel(
                building_id=building.id,
                floor_number=floor_no,
                floor_name=floor_name,
            )
            self.db.add(floor)
            await self.db.flush()

            unit_count = override.units_count if override is not None else data.units_per_floor
            prefix = override.unit_prefix.strip() if (override and override.unit_prefix) else ""

            for unit_idx in range(1, unit_count + 1):
                if prefix:
                    unit_number = f"{prefix}-{floor_no}{unit_idx:02d}" if not prefix.endswith("-") else f"{prefix}{floor_no}{unit_idx:02d}"
                else:
                    unit_number = f"{floor_no}{unit_idx:02d}"

                unit = UnitModel(
                    floor_id=floor.id,
                    unit_number=unit_number,
                )
                self.db.add(unit)

        society = await self.repo.get_society(society_id)
        if society and society.status == SocietyStatus.PENDING_SETUP.value:
            society.status = SocietyStatus.ACTIVE.value

        await self.db.flush()
        return building
