import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import ApiResponse
from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_platform_admin, require_society_admin
from app.authentication.models import UserModel
from app.societies.schemas import (
    SocietyCreate,
    SocietyUpdate,
    SocietyResponse,
    UserSocietyRoleAssign,
    UserSocietyRoleResponse,
)
from app.societies import routes
from app.societies.routes.common import safe_transaction

router = APIRouter(prefix="/societies")


@router.post("", response_model=ApiResponse[SocietyResponse], status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ApiResponse[SocietyResponse], status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_society(
    payload: SocietyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_platform_admin),
):
    service = routes.SocietyService(db)
    async with safe_transaction(db):
        res = await service.create_society(payload)
        return {"success": True, "message": "Society created successfully", "data": res}


@router.get("", response_model=ApiResponse[List[SocietyResponse]])
@router.get("/", response_model=ApiResponse[List[SocietyResponse]], include_in_schema=False)
async def list_societies(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    service = routes.SocietyService(db)
    res = await service.list_societies()
    return {"success": True, "message": "Societies retrieved successfully", "data": res}


@router.get("/{society_id}", response_model=ApiResponse[SocietyResponse])
async def get_society(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    service = routes.SocietyService(db)
    res = await service.get_society(society_id)
    return {"success": True, "message": "Society details retrieved successfully", "data": res}


@router.patch("/{society_id}", response_model=ApiResponse[SocietyResponse])
async def update_society(
    society_id: uuid.UUID,
    payload: SocietyUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_platform_admin),
):
    service = routes.SocietyService(db)
    async with safe_transaction(db):
        res = await service.update_society(society_id, payload)
        return {"success": True, "message": "Society updated successfully", "data": res}


@router.post("/{society_id}/assign-role", response_model=ApiResponse[UserSocietyRoleResponse], status_code=status.HTTP_200_OK)
async def assign_user_society_role(
    society_id: uuid.UUID,
    payload: UserSocietyRoleAssign,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    service = routes.SocietyService(db)
    async with safe_transaction(db):
        user_role = await service.repo.assign_user_society_role(
            society_id=society_id,
            user_id=payload.user_id,
            role=payload.role.value,
        )
        return {"success": True, "message": "User role assigned successfully", "data": user_role}
