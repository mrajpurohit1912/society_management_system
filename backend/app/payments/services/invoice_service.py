import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import structlog
from fastapi import HTTPException, status

from app.payments.services.base import BasePaymentService
from app.payments.models import MaintenanceInvoiceModel, InvoiceStatus
from app.payments.schemas import InvoiceCreate, BulkInvoiceGenerateRequest

logger = structlog.get_logger(__name__)


class InvoiceService(BasePaymentService):
    """
    Domain service for maintenance invoice lifecycle management.
    """

    async def create_invoice(
        self, society_id: uuid.UUID, data: InvoiceCreate
    ) -> MaintenanceInvoiceModel:
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
        return created

    async def bulk_generate_monthly_invoices(
        self, society_id: uuid.UUID, data: BulkInvoiceGenerateRequest
    ) -> List[MaintenanceInvoiceModel]:
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
        return created

    async def list_society_invoices(
        self,
        society_id: uuid.UUID,
        unit_id: Optional[uuid.UUID] = None,
        status_filter: Optional[str] = None,
        billing_period: Optional[str] = None,
    ) -> List[MaintenanceInvoiceModel]:
        return await self.payment_repo.list_invoices_by_society(
            society_id=society_id,
            unit_id=unit_id,
            status=status_filter,
            billing_period=billing_period,
        )

    async def get_invoice_details(
        self, invoice_id: uuid.UUID
    ) -> MaintenanceInvoiceModel:
        invoice = await self.payment_repo.get_invoice_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found.",
            )
        return invoice

    async def get_unit_dues(
        self, unit_id: uuid.UUID
    ) -> List[MaintenanceInvoiceModel]:
        return await self.payment_repo.list_invoices_by_unit(unit_id)
