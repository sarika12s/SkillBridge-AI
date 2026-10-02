"""Phase 8.2 schema for learning path milestone reconciliation

Revision ID: 0007_phase8_learning_reconcile
Revises: 0006_phase7_dashboard_versioning
Create Date: 2026-10-02 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0007_phase8_learning_reconcile'
down_revision: Union[str, None] = '0006_phase7_dashboard_versioning'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification provenance columns to learning_path_items
    op.add_column(
        'learning_path_items',
        sa.Column(
            'verified_by_resume_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resumes.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_learning_path_items_verified_by_resume_id',
        'learning_path_items',
        ['verified_by_resume_id'],
    )
    op.add_column(
        'learning_path_items',
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'learning_path_items',
        sa.Column('verification_method', sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('learning_path_items', 'verification_method')
    op.drop_column('learning_path_items', 'verified_at')
    op.drop_index('ix_learning_path_items_verified_by_resume_id', table_name='learning_path_items')
    op.drop_column('learning_path_items', 'verified_by_resume_id')
