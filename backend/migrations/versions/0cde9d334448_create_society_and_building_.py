"""create_society_and_building_infrastructure

Revision ID: 0cde9d334448
Revises: 6998d616ac99
Create Date: 2026-07-15 13:01:13.451104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cde9d334448'
down_revision: Union[str, Sequence[str], None] = '6998d616ac99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely using inspector."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'societies' not in existing_tables:
        op.create_table(
            'societies',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('registration_no', sa.String(length=50), nullable=False),
            sa.Column('address', sa.String(length=255), nullable=False),
            sa.Column('city', sa.String(length=100), nullable=False),
            sa.Column('state', sa.String(length=100), nullable=False),
            sa.Column('country', sa.String(length=100), nullable=False),
            sa.Column('zipcode', sa.String(length=20), nullable=False),
            sa.Column('email', sa.String(length=100), nullable=True),
            sa.Column('phone', sa.String(length=20), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('registration_no')
        )

    if 'buildings' not in existing_tables:
        op.create_table(
            'buildings',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('society_id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('address', sa.String(length=255), nullable=True),
            sa.Column('city', sa.String(length=100), nullable=True),
            sa.Column('state', sa.String(length=100), nullable=True),
            sa.Column('country', sa.String(length=100), nullable=True),
            sa.Column('zipcode', sa.String(length=20), nullable=True),
            sa.Column('email', sa.String(length=100), nullable=True),
            sa.Column('phone', sa.String(length=20), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['society_id'], ['societies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    if 'user_society_roles' not in existing_tables:
        op.create_table(
            'user_society_roles',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('society_id', sa.UUID(), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['society_id'], ['societies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    if 'floors' not in existing_tables:
        op.create_table(
            'floors',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('building_id', sa.UUID(), nullable=False),
            sa.Column('floor_number', sa.Integer(), nullable=False),
            sa.Column('floor_name', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['building_id'], ['buildings.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    if 'units' not in existing_tables:
        op.create_table(
            'units',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('floor_id', sa.UUID(), nullable=False),
            sa.Column('unit_number', sa.String(length=20), nullable=False),
            sa.Column('unit_type', sa.String(length=20), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['floor_id'], ['floors.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    if 'unit_residents' not in existing_tables:
        op.create_table(
            'unit_residents',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('unit_id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('residency_type', sa.String(length=30), nullable=False),
            sa.Column('is_primary_contact', sa.Boolean(), nullable=False),
            sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    if 'vehicles' not in existing_tables:
        op.create_table(
            'vehicles',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('unit_id', sa.UUID(), nullable=False),
            sa.Column('resident_id', sa.UUID(), nullable=True),
            sa.Column('vehicle_type', sa.String(length=20), nullable=False),
            sa.Column('registration_number', sa.String(length=30), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['resident_id'], ['unit_residents.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('registration_number')
        )


def downgrade() -> None:
    """Downgrade schema safely using inspector."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for t in ['vehicles', 'unit_residents', 'units', 'floors', 'user_society_roles', 'buildings', 'societies']:
        if t in existing_tables:
            op.drop_table(t)
