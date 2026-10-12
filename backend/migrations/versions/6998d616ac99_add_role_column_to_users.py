"""add_role_column_to_users

Revision ID: 6998d616ac99
Revises: 694bb60d91d6
Create Date: 2026-07-14 22:39:53.647790

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6998d616ac99'
down_revision: Union[str, Sequence[str], None] = '694bb60d91d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely using inspector."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'users' in existing_tables:
        user_cols = {c['name'] for c in inspector.get_columns('users')}
        if 'role' not in user_cols:
            op.add_column(
                'users',
                sa.Column('role', sa.String(length=20), nullable=False, server_default='member')
            )


def downgrade() -> None:
    """Downgrade schema safely using inspector."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'users' in existing_tables:
        user_cols = {c['name'] for c in inspector.get_columns('users')}
        if 'role' in user_cols:
            op.drop_column('users', 'role')
