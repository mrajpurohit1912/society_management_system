import uuid
from typing import Optional, List
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.authentication.dependencies import get_current_user, require_society_admin
from app.authentication.models import UserModel
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
    status_code=status.HTTP_201_CREATED,
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
    status_code=status.HTTP_201_CREATED,
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
    List maintenance invoices for a society with optional filters (unit, status, period).
    """
    service = InvoiceService(db)
    return await service.list_society_invoices(
        society_id=society_id,
        unit_id=unit_id,
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
    return await service.get_invoice_details(invoice_id)


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
    service = InvoiceService(db)
    return await service.get_unit_dues(unit_id)
