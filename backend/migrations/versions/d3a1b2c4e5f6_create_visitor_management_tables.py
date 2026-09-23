"""create visitor management tables

Revision ID: d3a1b2c4e5f6
Revises: b7e8f9a0c1d2
Create Date: 2026-09-21 15:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3a1b2c4e5f6'
down_revision: Union[str, Sequence[str], None] = 'b7e8f9a0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely using inspector."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. Create visitor_passes table if not exists
    if 'visitor_passes' not in existing_tables:
        op.create_table(
            'visitor_passes',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('society_id', sa.UUID(), nullable=False),
            sa.Column('unit_id', sa.UUID(), nullable=False),
            sa.Column('created_by_user_id', sa.UUID(), nullable=False),
            sa.Column('visitor_name', sa.String(length=100), nullable=False),
            sa.Column('visitor_phone', sa.String(length=20), nullable=False),
            sa.Column('visitor_type', sa.String(length=30), server_default='guest', nullable=False),
            sa.Column('passcode', sa.String(length=6), nullable=False),
            sa.Column('qr_code_token', sa.String(length=64), nullable=False),
            sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
            sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
            sa.Column('status', sa.String(length=30), server_default='active', nullable=False),
            sa.Column('vehicle_number', sa.String(length=30), nullable=True),
            sa.Column('expected_delivery_company', sa.String(length=100), nullable=True),
            sa.Column('notes', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.user_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['society_id'], ['societies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_visitor_passes_passcode'), 'visitor_passes', ['passcode'], unique=False)
        op.create_index(op.f('ix_visitor_passes_qr_code_token'), 'visitor_passes', ['qr_code_token'], unique=True)
    else:
        existing_indexes = {ix['name'] for ix in inspector.get_indexes('visitor_passes')}
        if 'ix_visitor_passes_passcode' not in existing_indexes:
            try:
                op.create_index(op.f('ix_visitor_passes_passcode'), 'visitor_passes', ['passcode'], unique=False)
            except Exception:
                pass
        if 'ix_visitor_passes_qr_code_token' not in existing_indexes:
            try:
                op.create_index(op.f('ix_visitor_passes_qr_code_token'), 'visitor_passes', ['qr_code_token'], unique=True)
            except Exception:
                pass

    # 2. Create visitor_logs table if not exists
    if 'visitor_logs' not in existing_tables:
        op.create_table(
            'visitor_logs',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('society_id', sa.UUID(), nullable=False),
            sa.Column('unit_id', sa.UUID(), nullable=False),
            sa.Column('pass_id', sa.UUID(), nullable=True),
            sa.Column('visitor_name', sa.String(length=100), nullable=False),
            sa.Column('visitor_phone', sa.String(length=20), nullable=False),
            sa.Column('visitor_type', sa.String(length=30), server_default='guest', nullable=False),
            sa.Column('entry_type', sa.String(length=30), server_default='pre_approved', nullable=False),
            sa.Column('status', sa.String(length=30), server_default='inside', nullable=False),
            sa.Column('vehicle_number', sa.String(length=30), nullable=True),
            sa.Column('company_name', sa.String(length=100), nullable=True),
            sa.Column('gate_number', sa.String(length=30), nullable=True),
            sa.Column('check_in_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('check_out_time', sa.DateTime(timezone=True), nullable=True),
            sa.Column('checked_in_by', sa.UUID(), nullable=True),
            sa.Column('checked_out_by', sa.UUID(), nullable=True),
            sa.Column('rejection_reason', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['checked_in_by'], ['users.user_id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['checked_out_by'], ['users.user_id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['pass_id'], ['visitor_passes.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['society_id'], ['societies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('visitor_logs')
    op.drop_index(op.f('ix_visitor_passes_qr_code_token'), table_name='visitor_passes')
    op.drop_index(op.f('ix_visitor_passes_passcode'), table_name='visitor_passes')
    op.drop_table('visitor_passes')
