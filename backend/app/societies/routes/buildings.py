import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import ApiResponse
from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_society_admin
from app.authentication.models import UserModel
from app.societies.schemas import (
    BuildingCreate,
    BuildingUpdate,
    BuildingResponse,
    FloorCreate,
    FloorResponse,
    BulkProvisionRequest,
)
from app.societies import routes
from app.societies.routes.common import safe_transaction

router = APIRouter(prefix="/societies")


@router.post("/{society_id}/buildings", response_model=ApiResponse[BuildingResponse], status_code=status.HTTP_201_CREATED)
async def create_building(
    society_id: uuid.UUID,
    payload: BuildingCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    service = routes.BuildingService(db)
    async with safe_transaction(db):
        res = await service.create_building(society_id, payload)
        return {"success": True, "message": "Building created successfully", "data": res}


@router.get("/{society_id}/buildings", response_model=ApiResponse[List[BuildingResponse]])
async def list_buildings(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    service = routes.BuildingService(db)
    res = await service.list_buildings(society_id)
    return {"success": True, "message": "Buildings retrieved successfully", "data": res}


@router.patch("/{society_id}/buildings/{building_id}", response_model=ApiResponse[BuildingResponse])
async def update_building(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: BuildingUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    service = routes.BuildingService(db)
    async with safe_transaction(db):
        res = await service.update_building(society_id, building_id, payload)
        return {"success": True, "message": "Building updated successfully", "data": res}


@router.post("/{society_id}/buildings/{building_id}/floors", response_model=ApiResponse[FloorResponse], status_code=status.HTTP_201_CREATED)
async def create_floor(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: FloorCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    b_service = routes.BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society.",
        )

    service = routes.FloorService(db)
    async with safe_transaction(db):
        res = await service.create_floor(building_id, payload)
        return {"success": True, "message": "Floor created successfully", "data": res}


@router.get("/{society_id}/buildings/{building_id}/floors", response_model=ApiResponse[List[FloorResponse]])
async def list_floors(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    b_service = routes.BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society.",
        )

    service = routes.FloorService(db)
    res = await service.list_floors(building_id)
    return {"success": True, "message": "Floors retrieved successfully", "data": res}


@router.post("/{society_id}/provision", response_model=ApiResponse[List[BuildingResponse]], status_code=status.HTTP_201_CREATED)
async def provision_society_structure(
    society_id: uuid.UUID,
    payload: BulkProvisionRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    service = routes.BulkProvisionService(db)
    async with safe_transaction(db):
        res = await service.provision_society_structure(society_id, payload)
        return {"success": True, "message": "Society structure provisioned successfully", "data": res}
