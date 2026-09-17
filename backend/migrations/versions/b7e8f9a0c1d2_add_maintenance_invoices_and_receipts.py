"""add maintenance_invoices, payment_receipts, and payment enhancements

Revision ID: b7e8f9a0c1d2
Revises: c4d2e8f19a0b
Create Date: 2026-09-17 15:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e8f9a0c1d2'
down_revision: Union[str, Sequence[str], None] = 'c4d2e8f19a0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create maintenance_invoices table
    op.create_table(
        'maintenance_invoices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('society_id', sa.UUID(), nullable=False),
        sa.Column('unit_id', sa.UUID(), nullable=False),
        sa.Column('billing_period', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('penalty_amount', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['society_id'], ['societies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Add columns to payments table
    op.add_column('payments', sa.Column('society_id', sa.UUID(), nullable=True))
    op.add_column('payments', sa.Column('invoice_id', sa.UUID(), nullable=True))
    op.add_column('payments', sa.Column('unit_id', sa.UUID(), nullable=True))
    op.add_column('payments', sa.Column('user_id', sa.UUID(), nullable=True))
    op.add_column('payments', sa.Column('payment_method', sa.String(length=30), server_default='offline_upi_neft', nullable=False))
    op.add_column('payments', sa.Column('transaction_reference', sa.String(length=100), nullable=True))
    op.add_column('payments', sa.Column('gateway_order_id', sa.String(length=100), nullable=True))
    op.add_column('payments', sa.Column('gateway_payment_id', sa.String(length=100), nullable=True))
    op.add_column('payments', sa.Column('approved_by', sa.UUID(), nullable=True))
    op.add_column('payments', sa.Column('rejection_reason', sa.String(length=255), nullable=True))
    op.add_column('payments', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('payments', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

    op.create_foreign_key('fk_payments_society_id', 'payments', 'societies', ['society_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_payments_invoice_id', 'payments', 'maintenance_invoices', ['invoice_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_payments_unit_id', 'payments', 'units', ['unit_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_payments_user_id', 'payments', 'users', ['user_id'], ['user_id'], ondelete='CASCADE')
    op.create_foreign_key('fk_payments_approved_by', 'payments', 'users', ['approved_by'], ['user_id'], ondelete='SET NULL')

    # 3. Create payment_receipts table
    op.create_table(
        'payment_receipts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('payment_id', sa.UUID(), nullable=False),
        sa.Column('receipt_number', sa.String(length=50), nullable=False),
        sa.Column('invoice_id', sa.UUID(), nullable=True),
        sa.Column('amount_paid', sa.Float(), nullable=False),
        sa.Column('payment_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('issued_to_name', sa.String(length=100), nullable=False),
        sa.Column('unit_number', sa.String(length=50), nullable=True),
        sa.Column('society_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_id'),
        sa.UniqueConstraint('receipt_number')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('payment_receipts')

    op.drop_constraint('fk_payments_approved_by', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_user_id', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_unit_id', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_invoice_id', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_society_id', 'payments', type_='foreignkey')

    op.drop_column('payments', 'updated_at')
    op.drop_column('payments', 'created_at')
    op.drop_column('payments', 'rejection_reason')
    op.drop_column('payments', 'approved_by')
    op.drop_column('payments', 'gateway_payment_id')
    op.drop_column('payments', 'gateway_order_id')
    op.drop_column('payments', 'transaction_reference')
    op.drop_column('payments', 'payment_method')
    op.drop_column('payments', 'user_id')
    op.drop_column('payments', 'unit_id')
    op.drop_column('payments', 'invoice_id')
    op.drop_column('payments', 'society_id')

    op.drop_table('maintenance_invoices')
