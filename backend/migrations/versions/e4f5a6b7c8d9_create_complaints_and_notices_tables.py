"""create complaints and notices tables

Revision ID: e4f5a6b7c8d9
Revises: d3a1b2c4e5f6
Create Date: 2026-09-21 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, Sequence[str], None] = 'd3a1b2c4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create complaint_tickets table
    op.create_table(
        'complaint_tickets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('society_id', sa.UUID(), nullable=False),
        sa.Column('unit_id', sa.UUID(), nullable=True),
        sa.Column('created_by_user_id', sa.UUID(), nullable=False),
        sa.Column('ticket_number', sa.String(length=30), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('scope', sa.String(length=30), server_default='personal_unit', nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='p3_medium', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='open', nullable=False),
        sa.Column('common_area_location', sa.String(length=100), nullable=True),
        sa.Column('photos', sa.JSON(), nullable=True),
        sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('assigned_to_user_id', sa.UUID(), nullable=True),
        sa.Column('assigned_vendor_name', sa.String(length=100), nullable=True),
        sa.Column('assigned_vendor_phone', sa.String(length=20), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolution_photos', sa.JSON(), nullable=True),
        sa.Column('resident_rating', sa.Integer(), nullable=True),
        sa.Column('resident_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['society_id'], ['societies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_complaint_tickets_ticket_number'), 'complaint_tickets', ['ticket_number'], unique=True)

    # 2. Create complaint_comments table
    op.create_table(
        'complaint_comments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('ticket_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('attachment_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ticket_id'], ['complaint_tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create notices table
    op.create_table(
        'notices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('society_id', sa.UUID(), nullable=False),
        sa.Column('created_by_user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), server_default='general', nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='normal', nullable=False),
        sa.Column('target_audience', sa.String(length=30), server_default='all', nullable=False),
        sa.Column('target_building_id', sa.UUID(), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['society_id'], ['societies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_building_id'], ['buildings.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Create notice_read_receipts table
    op.create_table(
        'notice_read_receipts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('notice_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['notice_id'], ['notices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('notice_id', 'user_id', name='uq_notice_user_read')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('notice_read_receipts')
    op.drop_table('notices')
    op.drop_table('complaint_comments')
    op.drop_index(op.f('ix_complaint_tickets_ticket_number'), table_name='complaint_tickets')
    op.drop_table('complaint_tickets')
