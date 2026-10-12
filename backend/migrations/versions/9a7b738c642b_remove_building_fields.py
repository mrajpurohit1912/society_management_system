"""remove building fields

Revision ID: 9a7b738c642b
Revises: 0cde9d334448
Create Date: 2026-07-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a7b738c642b'
down_revision: Union[str, Sequence[str], None] = '0cde9d334448'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely using inspector."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'buildings' in existing_tables:
        building_cols = {c['name'] for c in inspector.get_columns('buildings')}
        for col in ['address', 'city', 'state', 'country', 'zipcode', 'email', 'phone', 'status']:
            if col in building_cols:
                op.drop_column('buildings', col)


def downgrade() -> None:
    """Downgrade schema safely using inspector."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'buildings' in existing_tables:
        building_cols = {c['name'] for c in inspector.get_columns('buildings')}
        if 'status' not in building_cols:
            op.add_column('buildings', sa.Column('status', sa.String(length=20), nullable=False, server_default='active'))
        if 'phone' not in building_cols:
            op.add_column('buildings', sa.Column('phone', sa.String(length=20), nullable=True))
        if 'email' not in building_cols:
            op.add_column('buildings', sa.Column('email', sa.String(length=100), nullable=True))
        if 'zipcode' not in building_cols:
            op.add_column('buildings', sa.Column('zipcode', sa.String(length=20), nullable=True))
        if 'country' not in building_cols:
            op.add_column('buildings', sa.Column('country', sa.String(length=100), nullable=True))
        if 'state' not in building_cols:
            op.add_column('buildings', sa.Column('state', sa.String(length=100), nullable=True))
        if 'city' not in building_cols:
            op.add_column('buildings', sa.Column('city', sa.String(length=100), nullable=True))
        if 'address' not in building_cols:
            op.add_column('buildings', sa.Column('address', sa.String(length=255), nullable=True))
