import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from contextlib import asynccontextmanager
from app.core.schemas import ApiResponse
from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_platform_admin, require_society_admin
from app.authentication.models import UserModel
from app.societies.schemas import (
    SocietyCreate,
    SocietyUpdate,
    SocietyResponse,
    BuildingCreate,
    BuildingUpdate,
    BuildingResponse,
    FloorCreate,
    FloorResponse,
    UnitCreate,
    UnitUpdate,
    UnitResponse,
    ResidentAssign,
    ResidentResponse,
    VehicleRegister,
    VehicleResponse,
    UserSocietyRoleAssign,
    UserSocietyRoleResponse,
    BulkProvisionRequest
)
from app.societies.services import (
    SocietyService,
    BuildingService,
    FloorService,
    UnitService,
    ResidentService,
    VehicleService,
    BulkProvisionService,
    MembershipService
)

router = APIRouter(prefix="/societies", tags=["Society & Membership Management"])


@asynccontextmanager
async def safe_transaction(db: AsyncSession):
    if db.in_transaction():
        yield
        await db.commit()
    else:
        async with db.begin():
            yield


from pydantic import BaseModel, Field, field_validator

class RequestMembershipPayload(BaseModel):
    society_id: uuid.UUID
    unit_id: Optional[uuid.UUID] = None
    role: Optional[str] = Field(default="resident", json_schema_extra={"example": "resident"})

    @field_validator("unit_id", mode="before")
    @classmethod
    def empty_unit_id_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

class RejectMembershipPayload(BaseModel):
    reason: Optional[str] = None


# --- Membership Endpoints ---

@router.post("/membership/request", status_code=status.HTTP_201_CREATED)
async def request_membership(
    payload: RequestMembershipPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Resident Endpoint: Submit a membership request to join a specific society and flat unit.
    """
    service = MembershipService(db)
    async with safe_transaction(db):
        res = await service.request_membership(
            user_id=current_user.user_id,
            society_id=payload.society_id,
            unit_id=payload.unit_id,
            role=payload.role or "resident"
        )
        return {
            "success": True,
            "message": "Membership request submitted successfully. Waiting for Society Admin approval.",
            "data": {
                "membership_id": str(res.id),
                "society_id": str(res.society_id),
                "unit_id": str(res.unit_id) if res.unit_id else None,
                "status": res.status,
                "role": res.role,
            }
        }


@router.get("/membership/status")
async def get_membership_status(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Resident Endpoint: Fetch current user's society memberships and statuses.
    """
    service = MembershipService(db)
    memberships = await service.get_user_memberships(current_user.user_id)
    return {
        "success": True,
        "data": [
            {
                "membership_id": str(m.id),
                "society_id": str(m.society_id),
                "unit_id": str(m.unit_id) if m.unit_id else None,
                "role": m.role,
                "status": m.status,
            } for m in memberships
        ]
    }


@router.get("/{society_id}/membership/requests")
async def list_pending_membership_requests(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    """
    Society Admin Endpoint: List all pending membership requests for the society.
    """
    service = MembershipService(db)
    requests = await service.list_pending_requests(society_id)
    return {
        "success": True,
        "data": [
            {
                "membership_id": str(r.id),
                "user_id": str(r.user_id),
                "society_id": str(r.society_id),
                "unit_id": str(r.unit_id) if r.unit_id else None,
                "role": r.role,
                "status": r.status,
                "requested_at": r.created_at.isoformat() if r.created_at else None,
            } for r in requests
        ]
    }


@router.post("/{society_id}/membership/{membership_id}/approve")
async def approve_membership_request(
    society_id: uuid.UUID,
    membership_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    """
    Society Admin Endpoint: Approve a resident's membership request and trigger automated Resend email.
    """
    service = MembershipService(db)
    async with safe_transaction(db):
        res = await service.approve_membership(membership_id, approved_by_user_id=current_user.user_id)
        return {
            "success": True,
            "message": "Membership request approved successfully! Notification email sent via Resend.",
            "data": {
                "membership_id": str(res.id),
                "user_id": str(res.user_id),
                "status": res.status,
            }
        }


@router.post("/{society_id}/membership/{membership_id}/reject")
async def reject_membership_request(
    society_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: Optional[RejectMembershipPayload] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    """
    Society Admin Endpoint: Reject a resident's membership request and trigger automated Resend email.
    """
    reason = payload.reason if payload else None
    service = MembershipService(db)
    async with safe_transaction(db):
        res = await service.reject_membership(membership_id, approved_by_user_id=current_user.user_id, reason=reason)
        return {
            "success": True,
            "message": "Membership request rejected.",
            "data": {
                "membership_id": str(res.id),
                "user_id": str(res.user_id),
                "status": res.status,
            }
        }


# --- Existing Society Endpoints ---

@router.post("", response_model=ApiResponse[SocietyResponse], status_code=status.HTTP_201_CREATED)
async def create_society(
    payload: SocietyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_platform_admin)
):
    service = SocietyService(db)
    async with safe_transaction(db):
        res = await service.create_society(payload)
        return {"success": True, "message": "Society created successfully", "data": res}


@router.get("", response_model=ApiResponse[List[SocietyResponse]])
async def list_societies(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    service = SocietyService(db)
    res = await service.list_societies()
    return {"success": True, "message": "Societies retrieved successfully", "data": res}


@router.get("/{society_id}", response_model=ApiResponse[SocietyResponse])
async def get_society(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    service = SocietyService(db)
    res = await service.get_society(society_id)
    return {"success": True, "message": "Society details retrieved successfully", "data": res}


@router.patch("/{society_id}", response_model=ApiResponse[SocietyResponse])
async def update_society(
    society_id: uuid.UUID,
    payload: SocietyUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_platform_admin)
):
    service = SocietyService(db)
    async with safe_transaction(db):
        res = await service.update_society(society_id, payload)
        return {"success": True, "message": "Society updated successfully", "data": res}


@router.post("/{society_id}/assign-role", response_model=ApiResponse[UserSocietyRoleResponse], status_code=status.HTTP_200_OK)
async def assign_user_society_role(
    society_id: uuid.UUID,
    payload: UserSocietyRoleAssign,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    service = SocietyService(db)
    async with safe_transaction(db):
        user_role = await service.repo.assign_user_society_role(
            society_id=society_id,
            user_id=payload.user_id,
            role=payload.role.value
        )
        return {"success": True, "message": "User role assigned successfully", "data": user_role}


# --- Building Endpoints ---

@router.post("/{society_id}/buildings", response_model=ApiResponse[BuildingResponse], status_code=status.HTTP_201_CREATED)
async def create_building(
    society_id: uuid.UUID,
    payload: BuildingCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    service = BuildingService(db)
    async with safe_transaction(db):
        res = await service.create_building(society_id, payload)
        return {"success": True, "message": "Building created successfully", "data": res}


@router.get("/{society_id}/buildings", response_model=ApiResponse[List[BuildingResponse]])
async def list_buildings(
    society_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    service = BuildingService(db)
    res = await service.list_buildings(society_id)
    return {"success": True, "message": "Buildings retrieved successfully", "data": res}


@router.patch("/{society_id}/buildings/{building_id}", response_model=ApiResponse[BuildingResponse])
async def update_building(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: BuildingUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    service = BuildingService(db)
    async with safe_transaction(db):
        res = await service.update_building(society_id, building_id, payload)
        return {"success": True, "message": "Building updated successfully", "data": res}


# --- Floor Endpoints ---

@router.post("/{society_id}/buildings/{building_id}/floors", response_model=ApiResponse[FloorResponse], status_code=status.HTTP_201_CREATED)
async def create_floor(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    payload: FloorCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    b_service = BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society."
        )

    service = FloorService(db)
    async with safe_transaction(db):
        res = await service.create_floor(building_id, payload)
        return {"success": True, "message": "Floor created successfully", "data": res}


@router.get("/{society_id}/buildings/{building_id}/floors", response_model=ApiResponse[List[FloorResponse]])
async def list_floors(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    b_service = BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society."
        )

    service = FloorService(db)
    res = await service.list_floors(building_id)
    return {"success": True, "message": "Floors retrieved successfully", "data": res}


# --- Unit Endpoints ---

@router.post("/{society_id}/buildings/{building_id}/floors/{floor_id}/units", response_model=ApiResponse[UnitResponse], status_code=status.HTTP_201_CREATED)
async def create_unit(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    payload: UnitCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    f_service = FloorService(db)
    floor = await f_service.get_floor(floor_id)
    if floor.building_id != building_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Floor does not belong to the specified building."
        )

    b_service = BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society."
        )

    service = UnitService(db)
    async with safe_transaction(db):
        res = await service.create_unit(floor_id, payload)
        return {"success": True, "message": "Unit created successfully", "data": res}


@router.get("/{society_id}/buildings/{building_id}/floors/{floor_id}/units", response_model=ApiResponse[List[UnitResponse]])
async def list_units(
    society_id: uuid.UUID,
    building_id: uuid.UUID,
    floor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    f_service = FloorService(db)
    floor = await f_service.get_floor(floor_id)
    if floor.building_id != building_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Floor does not belong to the specified building."
        )

    b_service = BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society."
        )

    service = UnitService(db)
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
    current_user: UserModel = Depends(require_society_admin)
):
    f_service = FloorService(db)
    floor = await f_service.get_floor(floor_id)
    if floor.building_id != building_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Floor does not belong to the specified building."
        )

    b_service = BuildingService(db)
    building = await b_service.get_building(building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to the specified society."
        )

    service = UnitService(db)
    async with safe_transaction(db):
        res = await service.update_unit(floor_id, unit_id, payload)
        return {"success": True, "message": "Unit updated successfully", "data": res}


# --- Resident Endpoints ---

@router.post("/{society_id}/units/{unit_id}/residents", response_model=ApiResponse[ResidentResponse], status_code=status.HTTP_201_CREATED)
async def assign_resident(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    payload: ResidentAssign,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    u_service = UnitService(db)
    unit = await u_service.get_unit(unit_id)
    f_service = FloorService(db)
    floor = await f_service.get_floor(unit.floor_id)
    b_service = BuildingService(db)
    building = await b_service.get_building(floor.building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit does not belong to the specified society."
        )

    service = ResidentService(db)
    async with safe_transaction(db):
        res = await service.assign_resident(unit_id, payload)
        return {"success": True, "message": "Resident assigned successfully", "data": res}


@router.get("/{society_id}/units/{unit_id}/residents", response_model=ApiResponse[List[ResidentResponse]])
async def list_residents(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    u_service = UnitService(db)
    unit = await u_service.get_unit(unit_id)
    f_service = FloorService(db)
    floor = await f_service.get_floor(unit.floor_id)
    b_service = BuildingService(db)
    building = await b_service.get_building(floor.building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit does not belong to the specified society."
        )

    service = ResidentService(db)
    res = await service.list_residents(unit_id)
    return {"success": True, "message": "Residents retrieved successfully", "data": res}


# --- Vehicle Endpoints ---

@router.post("/{society_id}/units/{unit_id}/vehicles", response_model=ApiResponse[VehicleResponse], status_code=status.HTTP_201_CREATED)
async def register_vehicle(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    payload: VehicleRegister,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    u_service = UnitService(db)
    unit = await u_service.get_unit(unit_id)
    f_service = FloorService(db)
    floor = await f_service.get_floor(unit.floor_id)
    b_service = BuildingService(db)
    building = await b_service.get_building(floor.building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit does not belong to the specified society."
        )

    service = VehicleService(db)
    async with safe_transaction(db):
        res = await service.register_vehicle(unit_id, payload)
        return {"success": True, "message": "Vehicle registered successfully", "data": res}


@router.get("/{society_id}/units/{unit_id}/vehicles", response_model=ApiResponse[List[VehicleResponse]])
async def list_vehicles(
    society_id: uuid.UUID,
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user)
):
    u_service = UnitService(db)
    unit = await u_service.get_unit(unit_id)
    f_service = FloorService(db)
    floor = await f_service.get_floor(unit.floor_id)
    b_service = BuildingService(db)
    building = await b_service.get_building(floor.building_id)
    if building.society_id != society_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit does not belong to the specified society."
        )

    service = VehicleService(db)
    res = await service.list_vehicles(unit_id)
    return {"success": True, "message": "Vehicles retrieved successfully", "data": res}


# --- Bulk Provisioning Endpoints ---

@router.post("/{society_id}/provision", response_model=ApiResponse[List[BuildingResponse]], status_code=status.HTTP_201_CREATED)
async def provision_society_structure(
    society_id: uuid.UUID,
    payload: BulkProvisionRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin)
):
    service = BulkProvisionService(db)
    async with safe_transaction(db):
        res = await service.provision_society_structure(society_id, payload)
        return {"success": True, "message": "Society structure provisioned successfully", "data": res}
