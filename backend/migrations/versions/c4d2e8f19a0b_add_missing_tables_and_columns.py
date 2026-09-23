"""add activation_tokens subscriptions society_leads and missing columns

Revision ID: c4d2e8f19a0b
Revises: 9a7b738c642b
Create Date: 2026-09-17 15:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d2e8f19a0b'
down_revision: Union[str, Sequence[str], None] = '9a7b738c642b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely using inspector to handle existing tables/columns."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. Create activation_tokens table if not exists
    if 'activation_tokens' not in existing_tables:
        op.create_table(
            'activation_tokens',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('token', sa.String(length=255), nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('token')
        )
        op.create_index(op.f('ix_activation_tokens_token'), 'activation_tokens', ['token'], unique=True)
    else:
        existing_indexes = {ix['name'] for ix in inspector.get_indexes('activation_tokens')}
        if 'ix_activation_tokens_token' not in existing_indexes:
            try:
                op.create_index(op.f('ix_activation_tokens_token'), 'activation_tokens', ['token'], unique=True)
            except Exception:
                pass

    # 2. Create subscriptions table if not exists
    if 'subscriptions' not in existing_tables:
        op.create_table(
            'subscriptions',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('society_id', sa.UUID(), nullable=False),
            sa.Column('plan', sa.String(length=50), server_default='GOLD', nullable=False),
            sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
            sa.Column('start_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('max_admins', sa.Integer(), server_default='5', nullable=False),
            sa.Column('max_storage_gb', sa.Integer(), server_default='10', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['society_id'], ['societies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('society_id')
        )

    # 3. Create society_leads table if not exists
    if 'society_leads' not in existing_tables:
        op.create_table(
            'society_leads',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('organization_name', sa.String(length=255), nullable=False),
            sa.Column('primary_contact_name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('mobile', sa.String(length=50), nullable=False),
            sa.Column('city', sa.String(length=100), nullable=False),
            sa.Column('expected_flats', sa.Integer(), nullable=True),
            sa.Column('expected_admins', sa.Integer(), nullable=True),
            sa.Column('comments', sa.String(length=500), nullable=True),
            sa.Column('status', sa.String(length=30), server_default='lead_created', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )

    # 4. Add missing columns to users if not present
    user_columns = {c['name'] for c in inspector.get_columns('users')}
    if 'email_verified' not in user_columns:
        op.add_column('users', sa.Column('email_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    if 'status' not in user_columns:
        op.add_column('users', sa.Column('status', sa.String(length=30), server_default='registered', nullable=False))

    # 5. Add missing columns to user_society_roles if not present
    role_columns = {c['name'] for c in inspector.get_columns('user_society_roles')}
    if 'unit_id' not in role_columns:
        op.add_column('user_society_roles', sa.Column('unit_id', sa.UUID(), nullable=True))
    if 'status' not in role_columns:
        op.add_column('user_society_roles', sa.Column('status', sa.String(length=30), server_default='approved', nullable=False))
    if 'approved_by' not in role_columns:
        op.add_column('user_society_roles', sa.Column('approved_by', sa.UUID(), nullable=True))

    role_fks = {fk['name'] for fk in inspector.get_foreign_keys('user_society_roles')}
    if 'fk_user_society_roles_unit_id' not in role_fks and 'unit_id' in role_columns:
        try:
            op.create_foreign_key(
                'fk_user_society_roles_unit_id',
                'user_society_roles',
                'units',
                ['unit_id'],
                ['id'],
                ondelete='SET NULL'
            )
        except Exception:
            pass
    if 'fk_user_society_roles_approved_by' not in role_fks and 'approved_by' in role_columns:
        try:
            op.create_foreign_key(
                'fk_user_society_roles_approved_by',
                'user_society_roles',
                'users',
                ['approved_by'],
                ['user_id'],
                ondelete='SET NULL'
            )
        except Exception:
            pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_user_society_roles_approved_by', 'user_society_roles', type_='foreignkey')
    op.drop_constraint('fk_user_society_roles_unit_id', 'user_society_roles', type_='foreignkey')
    op.drop_column('user_society_roles', 'approved_by')
    op.drop_column('user_society_roles', 'status')
    op.drop_column('user_society_roles', 'unit_id')

    op.drop_column('users', 'status')
    op.drop_column('users', 'email_verified')

    op.drop_table('society_leads')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_activation_tokens_token'), table_name='activation_tokens')
    op.drop_table('activation_tokens')
