import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import ApiResponse
from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_society_admin
from app.authentication.models import UserModel
from app.societies.schemas import (
    UnitCreate,
    UnitUpdate,
    UnitResponse,
)
from app.societies import routes
from app.societies.routes.common import safe_transaction

router = APIRouter(prefix="/societies")


@router.post("/{society_id}/buildings/{building_id}/floors/{floor_id}/units", response_model=ApiResponse[UnitResponse], status_code=status.HTTP_201_CREATED)
async def create_unit(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    payload: UnitCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    f_service = routes.FloorService(db)
    floor = await f_service.get_floor(floor_id)
    if floor.building_id != building_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Floor does not belong to the specified building.",
        )

    b_service = routes.BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society.",
        )

    service = routes.UnitService(db)
    async with safe_transaction(db):
        res = await service.create_unit(floor_id, payload)
        return {"success": True, "message": "Unit created successfully", "data": res}


@router.get("/{society_id}/buildings/{building_id}/floors/{floor_id}/units", response_model=ApiResponse[List[UnitResponse]])
async def list_units(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    f_service = routes.FloorService(db)
    floor = await f_service.get_floor(floor_id)
    if floor.building_id != building_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Floor does not belong to the specified building.",
        )

    b_service = routes.BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society.",
        )

    service = routes.UnitService(db)
    res = await service.list_units(floor_id)
    return {"success": True, "message": "Units retrieved successfully", "data": res}


@router.patch("/{society_id}/buildings/{building_id}/floors/{floor_id}/units/{unit_id}", response_model=ApiResponse[UnitResponse])
async def update_unit(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    unit_id: uuid.UUID,
    payload: UnitUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    f_service = routes.FloorService(db)
    floor = await f_service.get_floor(floor_id)
    if floor.building_id != building_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Floor does not belong to the specified building.",
        )

    b_service = routes.BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society.",
        )

    service = routes.UnitService(db)
    async with safe_transaction(db):
        res = await service.update_unit(unit_id, payload)
        return {"success": True, "message": "Unit updated successfully", "data": res}
