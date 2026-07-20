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
    """Upgrade schema."""
    op.drop_column('buildings', 'address')
    op.drop_column('buildings', 'city')
    op.drop_column('buildings', 'state')
    op.drop_column('buildings', 'country')
    op.drop_column('buildings', 'zipcode')
    op.drop_column('buildings', 'email')
    op.drop_column('buildings', 'phone')
    op.drop_column('buildings', 'status')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('buildings', sa.Column('status', sa.String(length=20), nullable=False, server_default='active'))
    op.add_column('buildings', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('buildings', sa.Column('email', sa.String(length=100), nullable=True))
    op.add_column('buildings', sa.Column('zipcode', sa.String(length=20), nullable=True))
    op.add_column('buildings', sa.Column('country', sa.String(length=100), nullable=True))
    op.add_column('buildings', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('buildings', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('buildings', sa.Column('address', sa.String(length=255), nullable=True))
