import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import structlog
from fastapi import HTTPException, status

from app.payments.services.base import BasePaymentService
from app.payments.models import MaintenanceInvoiceModel, InvoiceStatus
from app.payments.schemas import InvoiceCreate, BulkInvoiceGenerateRequest, InvoiceResponse

logger = structlog.get_logger(__name__)


class InvoiceService(BasePaymentService):
    """
    Domain service for maintenance invoice lifecycle management.
    """

    def _format_invoice(
        self,
        invoice: MaintenanceInvoiceModel,
        resident_lookup: Optional[Dict[uuid.UUID, Dict[str, Any]]] = None,
    ) -> InvoiceResponse:
        unit = getattr(invoice, "unit", None)
        unit_number = unit.unit_number if unit else None
        floor_number = (
            unit.floor.floor_number
            if (unit and hasattr(unit, "floor") and unit.floor)
            else None
        )
        building_name = (
            unit.floor.building.name
            if (
                unit
                and hasattr(unit, "floor")
                and unit.floor
                and hasattr(unit.floor, "building")
                and unit.floor.building
            )
            else None
        )

        resident_name = None
        resident_email = None
        resident_phone = None
        residency_type = None

        if unit and hasattr(unit, "residents") and unit.residents:
            primary_res = next((r for r in unit.residents if getattr(r, "is_primary_contact", False)), None)
            if not primary_res:
                primary_res = next((r for r in unit.residents if getattr(r, "status", "") == "active"), unit.residents[0])

            if primary_res and hasattr(primary_res, "user") and primary_res.user:
                resident_name = f"{primary_res.user.first_name} {primary_res.user.last_name}".strip()
                residency_type = getattr(primary_res, "residency_type", None)
                if hasattr(primary_res.user, "credentials") and primary_res.user.credentials:
                    for c in primary_res.user.credentials:
                        if not resident_email and (c.provider in ("email", "google") or "@" in c.identifier):
                            resident_email = c.identifier
                        elif not resident_phone and (c.provider == "phone" or c.identifier.replace("+", "").replace(" ", "").isdigit()):
                            resident_phone = c.identifier
                    if not resident_email and not resident_phone and primary_res.user.credentials:
                        first_c = primary_res.user.credentials[0].identifier
                        if "@" in first_c:
                            resident_email = first_c
                        else:
                            resident_phone = first_c

        if not resident_name and resident_lookup and invoice.unit_id in resident_lookup:
            res_info = resident_lookup[invoice.unit_id]
            resident_name = res_info.get("resident_name")
            resident_email = res_info.get("resident_email")
            resident_phone = res_info.get("resident_phone")
            residency_type = res_info.get("residency_type")

        return InvoiceResponse(
            id=invoice.id,
            society_id=invoice.society_id,
            unit_id=invoice.unit_id,
            billing_period=invoice.billing_period,
            title=invoice.title,
            description=invoice.description,
            amount=invoice.amount,
            due_date=invoice.due_date,
            penalty_amount=invoice.penalty_amount,
            status=invoice.status,
            created_at=invoice.created_at,
            unit_number=unit_number,
            building_name=building_name,
            floor_number=floor_number,
            resident_name=resident_name,
            resident_email=resident_email,
            resident_phone=resident_phone,
            residency_type=residency_type,
        )

    async def create_invoice(
        self, society_id: uuid.UUID, data: InvoiceCreate
    ) -> InvoiceResponse:
        society = await self.society_repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Society not found.",
            )

        unit = await self.society_repo.get_unit(data.unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found.",
            )

        existing = await self.payment_repo.get_invoice_by_unit_and_period(
            data.unit_id, data.billing_period
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An invoice for unit {unit.unit_number} for period '{data.billing_period}' already exists.",
            )

        invoice = MaintenanceInvoiceModel(
            society_id=society_id,
            unit_id=data.unit_id,
            billing_period=data.billing_period,
            title=data.title,
            description=data.description,
            amount=data.amount,
            due_date=data.due_date,
            status=InvoiceStatus.PENDING.value,
        )
        created = await self.payment_repo.create_invoice(invoice)
        logger.info(
            "payments.invoice_created",
            invoice_id=str(created.id),
            society_id=str(society_id),
            unit_id=str(data.unit_id),
            amount=data.amount,
        )
        return await self.get_invoice_details(created.id)

    async def bulk_generate_monthly_invoices(
        self, society_id: uuid.UUID, data: BulkInvoiceGenerateRequest
    ) -> List[InvoiceResponse]:
        society = await self.society_repo.get_society(society_id)
        if not society:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Society not found.",
            )

        units = await self.society_repo.list_all_units_in_society(
            society_id=society_id, building_id=data.building_id
        )
        if not units:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No units found in the specified society / building for invoice generation.",
            )

        due_date = datetime.now(timezone.utc) + timedelta(days=data.due_date_days)
        invoices_to_create = []

        for unit in units:
            existing = await self.payment_repo.get_invoice_by_unit_and_period(
                unit.id, data.billing_period
            )
            if not existing:
                invoices_to_create.append(
                    MaintenanceInvoiceModel(
                        society_id=society_id,
                        unit_id=unit.id,
                        billing_period=data.billing_period,
                        title=data.title,
                        description=data.description,
                        amount=data.amount,
                        due_date=due_date,
                        status=InvoiceStatus.PENDING.value,
                    )
                )

        if not invoices_to_create:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"All units already have invoices generated for period '{data.billing_period}'.",
            )

        created = await self.payment_repo.bulk_create_invoices(invoices_to_create)
        logger.info(
            "payments.bulk_invoices_generated",
            society_id=str(society_id),
            period=data.billing_period,
            count=len(created),
        )
        resident_map = await self.payment_repo.get_unit_residents_map(society_id)
        return [self._format_invoice(inv, resident_map) for inv in created]

    async def list_society_invoices(
        self,
        society_id: uuid.UUID,
        unit_id: Optional[uuid.UUID] = None,
        status_filter: Optional[str] = None,
        billing_period: Optional[str] = None,
    ) -> List[InvoiceResponse]:
        invoices = await self.payment_repo.list_invoices_by_society(
            society_id=society_id,
            unit_id=unit_id,
            status=status_filter,
            billing_period=billing_period,
        )
        resident_map = await self.payment_repo.get_unit_residents_map(society_id)
        return [self._format_invoice(inv, resident_map) for inv in invoices]

    async def get_invoice_details(
        self, invoice_id: uuid.UUID
    ) -> InvoiceResponse:
        invoice = await self.payment_repo.get_invoice_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found.",
            )
        resident_map = await self.payment_repo.get_unit_residents_map(invoice.society_id)
        return self._format_invoice(invoice, resident_map)

    async def get_unit_dues(
        self, unit_id: uuid.UUID
    ) -> List[InvoiceResponse]:
        invoices = await self.payment_repo.list_invoices_by_unit(unit_id)
        society_id = invoices[0].society_id if invoices else None
        resident_map = await self.payment_repo.get_unit_residents_map(society_id) if society_id else None
        return [self._format_invoice(inv, resident_map) for inv in invoices]
