import uuid
from typing import Optional, List
import structlog
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_society_admin
from app.authentication.models import UserModel
from app.societies.models import (
    UserSocietyRoleModel,
    SocietyRole,
    UnitResidentModel,
    BuildingModel,
    FloorModel,
    UnitModel,
)
from app.payments.schemas import (
    InvoiceCreate,
    BulkInvoiceGenerateRequest,
    InvoiceResponse,
)
from app.payments.services.invoice_service import InvoiceService
from app.payments.routes.common import safe_transaction

router = APIRouter(tags=["Maintenance Invoices"])
logger = structlog.get_logger(__name__)


@router.post(
    "/societies/{society_id}/invoices",
    response_model=InvoiceResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_maintenance_invoice(
    society_id: uuid.UUID,
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Society Admin Endpoint: Generate a maintenance invoice for a specific unit.
    """
    service = InvoiceService(db)
    async with safe_transaction(db):
        invoice = await service.create_invoice(society_id, payload)
    return invoice


@router.post(
    "/societies/{society_id}/invoices/bulk-generate",
    response_model=List[InvoiceResponse],
    status_code=http_status.HTTP_201_CREATED,
)
async def bulk_generate_monthly_invoices(
    society_id: uuid.UUID,
    payload: BulkInvoiceGenerateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(require_society_admin),
):
    """
    Society Admin Endpoint: Automatically generate monthly maintenance invoices
    for all units in a society or specific building.
    """
    service = InvoiceService(db)
    async with safe_transaction(db):
        invoices = await service.bulk_generate_monthly_invoices(society_id, payload)
    return invoices


@router.get(
    "/societies/{society_id}/invoices",
    response_model=List[InvoiceResponse],
)
async def list_society_invoices(
    society_id: uuid.UUID,
    unit_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    billing_period: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """
    List maintenance invoices for a society with strict role-based isolation:
    - Platform Admins and Society Admins/Committee can view all or filter by unit.
    - Residents can ONLY view invoices for their own assigned unit.
    """
    is_platform_admin = current_user.role in ("platform_admin", "admin")
    effective_unit_id = unit_id

    if not is_platform_admin:
        # Check society membership and role
        query = select(UserSocietyRoleModel).where(
            UserSocietyRoleModel.user_id == current_user.user_id,
            UserSocietyRoleModel.society_id == society_id,
        )
        res = await db.execute(query)
        membership = res.scalar_one_or_none()

        admin_roles = (SocietyRole.ADMIN.value, SocietyRole.SOCIETY_ADMIN.value, SocietyRole.COMMITTEE.value)
        if membership and membership.role in admin_roles:
            # Society admin/committee can list all or filter by any unit
            pass
        else:
            # Resident access: strictly enforce filtering by the resident's assigned unit
            resident_unit_id = membership.unit_id if membership else None
            if not resident_unit_id:
                # Check UnitResidentModel fallback
                res_link = await db.execute(
                    select(UnitResidentModel.unit_id)
                    .join(UnitModel, UnitModel.id == UnitResidentModel.unit_id)
                    .join(FloorModel, FloorModel.id == UnitModel.floor_id)
                    .join(BuildingModel, BuildingModel.id == FloorModel.building_id)
                    .where(
                        UnitResidentModel.user_id == current_user.user_id,
                        BuildingModel.society_id == society_id,
                    )
                )
                resident_unit_id = res_link.scalar_one_or_none()

            if not resident_unit_id:
                # Resident has no flat assigned yet in this society -> return empty invoices
                return []

            if unit_id and unit_id != resident_unit_id:
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You can only view maintenance dues for your assigned flat.",
                )
            effective_unit_id = resident_unit_id

    service = InvoiceService(db)
    return await service.list_society_invoices(
        society_id=society_id,
        unit_id=effective_unit_id,
        status_filter=status,
        billing_period=billing_period,
    )


@router.get(
    "/societies/{society_id}/invoices/{invoice_id}",
    response_model=InvoiceResponse,
)
async def get_invoice_details(
    society_id: uuid.UUID,
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get detailed breakdown of a specific maintenance invoice.
    """
    service = InvoiceService(db)
    invoice = await service.get_invoice_details(invoice_id)
    if not invoice or invoice.society_id != society_id:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

    is_platform_admin = current_user.role in ("platform_admin", "admin")
    if not is_platform_admin:
        query = select(UserSocietyRoleModel).where(
            UserSocietyRoleModel.user_id == current_user.user_id,
            UserSocietyRoleModel.society_id == society_id,
        )
        res = await db.execute(query)
        membership = res.scalar_one_or_none()
        admin_roles = (SocietyRole.ADMIN.value, SocietyRole.SOCIETY_ADMIN.value, SocietyRole.COMMITTEE.value)
        if membership and membership.role in admin_roles:
            pass
        elif membership and membership.unit_id and membership.unit_id != invoice.unit_id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot view invoices for other flats.",
            )

    return invoice


@router.get(
    "/units/{unit_id}/dues",
    response_model=List[InvoiceResponse],
)
async def get_unit_dues(
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Resident / Admin Endpoint: Fetch all active and past dues for a flat / unit.
    """
    is_platform_admin = current_user.role in ("platform_admin", "admin")
    if not is_platform_admin:
        query = select(UserSocietyRoleModel).where(
            UserSocietyRoleModel.user_id == current_user.user_id,
        )
        res = await db.execute(query)
        memberships = list(res.scalars().all())
        admin_roles = (SocietyRole.ADMIN.value, SocietyRole.SOCIETY_ADMIN.value, SocietyRole.COMMITTEE.value)
        is_admin = any(m.role in admin_roles for m in memberships)
        if not is_admin:
            user_units = {m.unit_id for m in memberships if m.unit_id}
            res_links = await db.execute(
                select(UnitResidentModel.unit_id).where(UnitResidentModel.user_id == current_user.user_id)
            )
            for uid in res_links.scalars().all():
                if uid:
                    user_units.add(uid)
            if user_units and unit_id not in user_units:
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You can only view maintenance dues for your own unit.",
                )

    service = InvoiceService(db)
    return await service.get_unit_dues(unit_id)
