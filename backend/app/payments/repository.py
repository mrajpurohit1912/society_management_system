import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.payments.models import (
    MaintenanceInvoiceModel,
    PaymentModel,
    PaymentReceiptModel,
    InvoiceStatus,
    PaymentStatus,
)


class PaymentRepository:
    """
    Data Access Layer (Repository Pattern) for Payments & Maintenance Billing.
    Encapsulates all database operations using SQLAlchemy 2.0 Async Session.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------
    # Invoices
    # ---------------------------------------------------------

    async def create_invoice(
        self, invoice: MaintenanceInvoiceModel
    ) -> MaintenanceInvoiceModel:
        self.db.add(invoice)
        await self.db.flush()
        return invoice

    async def bulk_create_invoices(
        self, invoices: List[MaintenanceInvoiceModel]
    ) -> List[MaintenanceInvoiceModel]:
        self.db.add_all(invoices)
        await self.db.flush()
        return invoices

    async def get_invoice_by_id(
        self, invoice_id: uuid.UUID
    ) -> Optional[MaintenanceInvoiceModel]:
        stmt = (
            select(MaintenanceInvoiceModel)
            .where(MaintenanceInvoiceModel.id == invoice_id)
            .options(
                selectinload(MaintenanceInvoiceModel.society),
                selectinload(MaintenanceInvoiceModel.unit),
                selectinload(MaintenanceInvoiceModel.payments),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_invoice_by_unit_and_period(
        self, unit_id: uuid.UUID, billing_period: str
    ) -> Optional[MaintenanceInvoiceModel]:
        stmt = select(MaintenanceInvoiceModel).where(
            MaintenanceInvoiceModel.unit_id == unit_id,
            MaintenanceInvoiceModel.billing_period == billing_period,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_invoices_by_society(
        self,
        society_id: uuid.UUID,
        unit_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        billing_period: Optional[str] = None,
    ) -> List[MaintenanceInvoiceModel]:
        stmt = (
            select(MaintenanceInvoiceModel)
            .where(MaintenanceInvoiceModel.society_id == society_id)
            .order_by(MaintenanceInvoiceModel.created_at.desc())
        )
        if unit_id:
            stmt = stmt.where(MaintenanceInvoiceModel.unit_id == unit_id)
        if status:
            stmt = stmt.where(MaintenanceInvoiceModel.status == status)
        if billing_period:
            stmt = stmt.where(MaintenanceInvoiceModel.billing_period == billing_period)

        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_invoices_by_unit(
        self, unit_id: uuid.UUID
    ) -> List[MaintenanceInvoiceModel]:
        stmt = (
            select(MaintenanceInvoiceModel)
            .where(MaintenanceInvoiceModel.unit_id == unit_id)
            .order_by(MaintenanceInvoiceModel.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_invoice(
        self, invoice: MaintenanceInvoiceModel
    ) -> MaintenanceInvoiceModel:
        await self.db.flush()
        return invoice

    # ---------------------------------------------------------
    # Payments
    # ---------------------------------------------------------

    async def create_payment(self, payment: PaymentModel) -> PaymentModel:
        self.db.add(payment)
        await self.db.flush()
        return payment

    async def get_payment_by_id(
        self, payment_id: uuid.UUID
    ) -> Optional[PaymentModel]:
        stmt = (
            select(PaymentModel)
            .where(PaymentModel.id == payment_id)
            .options(
                selectinload(PaymentModel.invoice),
                selectinload(PaymentModel.receipt),
                selectinload(PaymentModel.user),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_payments_by_society(
        self, society_id: uuid.UUID, status: Optional[str] = None
    ) -> List[PaymentModel]:
        stmt = (
            select(PaymentModel)
            .where(PaymentModel.society_id == society_id)
            .order_by(PaymentModel.created_at.desc())
        )
        if status:
            stmt = stmt.where(PaymentModel.status == status)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_payments_by_unit(
        self, unit_id: uuid.UUID
    ) -> List[PaymentModel]:
        stmt = (
            select(PaymentModel)
            .where(PaymentModel.unit_id == unit_id)
            .order_by(PaymentModel.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_pending_approvals(
        self, society_id: uuid.UUID
    ) -> List[PaymentModel]:
        stmt = (
            select(PaymentModel)
            .where(
                PaymentModel.society_id == society_id,
                PaymentModel.status == PaymentStatus.PENDING_APPROVAL.value,
            )
            .order_by(PaymentModel.created_at.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_payment(self, payment: PaymentModel) -> PaymentModel:
        await self.db.flush()
        return payment

    # ---------------------------------------------------------
    # Receipts
    # ---------------------------------------------------------

    async def create_receipt(
        self, receipt: PaymentReceiptModel
    ) -> PaymentReceiptModel:
        self.db.add(receipt)
        await self.db.flush()
        return receipt

    async def get_receipt_by_payment_id(
        self, payment_id: uuid.UUID
    ) -> Optional[PaymentReceiptModel]:
        stmt = select(PaymentReceiptModel).where(
            PaymentReceiptModel.payment_id == payment_id
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_receipt_by_number(
        self, receipt_number: str
    ) -> Optional[PaymentReceiptModel]:
        stmt = select(PaymentReceiptModel).where(
            PaymentReceiptModel.receipt_number == receipt_number
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    # ---------------------------------------------------------
    # Collection Summary / Analytics
    # ---------------------------------------------------------

    async def get_collection_summary(
        self, society_id: uuid.UUID
    ) -> Dict[str, Any]:
        # Sum of all invoiced amounts
        invoiced_stmt = select(func.coalesce(func.sum(MaintenanceInvoiceModel.amount), 0.0)).where(
            MaintenanceInvoiceModel.society_id == society_id
        )
        total_invoiced = await self.db.scalar(invoiced_stmt) or 0.0

        # Sum of completed payments
        collected_stmt = select(func.coalesce(func.sum(PaymentModel.amount), 0.0)).where(
            PaymentModel.society_id == society_id,
            PaymentModel.status == PaymentStatus.COMPLETED.value,
        )
        total_collected = await self.db.scalar(collected_stmt) or 0.0

        # Pending approval count
        pending_approval_stmt = select(func.count(PaymentModel.id)).where(
            PaymentModel.society_id == society_id,
            PaymentModel.status == PaymentStatus.PENDING_APPROVAL.value,
        )
        pending_approval_count = await self.db.scalar(pending_approval_stmt) or 0

        # Pending invoice amount
        pending_stmt = select(func.coalesce(func.sum(MaintenanceInvoiceModel.amount), 0.0)).where(
            MaintenanceInvoiceModel.society_id == society_id,
            MaintenanceInvoiceModel.status == InvoiceStatus.PENDING.value,
        )
        total_pending = await self.db.scalar(pending_stmt) or 0.0

        return {
            "total_invoiced": float(total_invoiced),
            "total_collected": float(total_collected),
            "total_pending": float(total_pending),
            "pending_approval_count": int(pending_approval_count),
        }
