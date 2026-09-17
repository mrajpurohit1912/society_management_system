import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import ApiResponse
from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_society_admin
from app.authentication.models import UserModel
from app.societies.schemas import (
    ResidentAssign,
    ResidentResponse,
    VehicleRegister,
    VehicleResponse,
)
from app.societies import routes
from app.societies.routes.common import safe_transaction

router = APIRouter(prefix="/societies")


async def _verify_unit_society(db: AsyncSession, society_id: uuid.UUID, unit_id: uuid.UUID):
    u_service = routes.UnitService(db)
    unit = await u_service.get_unit(unit_id)
    f_service = routes.FloorService(db)
    floor = await f_service.get_floor(unit.floor_id)
    b_service = routes.BuildingService(db)
    building = await b_service.get_building(floor.building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit does not belong to the specified society.",
        )
    return unit


@router.post("/{society_id}/units/{unit_id}/residents", response_model=ApiResponse[ResidentResponse], status_code=status.HTTP_201_CREATED)
async def assign_resident(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    payload: ResidentAssign,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    await _verify_unit_society(db, society_id, unit_id)
    service = routes.ResidentService(db)
    async with safe_transaction(db):
        res = await service.assign_resident(unit_id, payload)
        return {"success": True, "message": "Resident assigned successfully", "data": res}


@router.get("/{society_id}/units/{unit_id}/residents", response_model=ApiResponse[List[ResidentResponse]])
async def list_residents(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    await _verify_unit_society(db, society_id, unit_id)
    service = routes.ResidentService(db)
    res = await service.list_residents(unit_id)
    return {"success": True, "message": "Residents retrieved successfully", "data": res}


@router.post("/{society_id}/units/{unit_id}/vehicles", response_model=ApiResponse[VehicleResponse], status_code=status.HTTP_201_CREATED)
async def register_vehicle(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    payload: VehicleRegister,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    await _verify_unit_society(db, society_id, unit_id)
    service = routes.VehicleService(db)
    async with safe_transaction(db):
        res = await service.register_vehicle(unit_id, payload)
        return {"success": True, "message": "Vehicle registered successfully", "data": res}


@router.get("/{society_id}/units/{unit_id}/vehicles", response_model=ApiResponse[List[VehicleResponse]])
async def list_vehicles(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    await _verify_unit_society(db, society_id, unit_id)
    service = routes.VehicleService(db)
    res = await service.list_vehicles(unit_id)
    return {"success": True, "message": "Vehicles retrieved successfully", "data": res}
