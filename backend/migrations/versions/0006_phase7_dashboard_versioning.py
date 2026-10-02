"""Phase 7 schema for resume version tracking and dashboard analytics

Revision ID: 0006_phase7_dashboard_versioning
Revises: 0005_phase6_career_learning
Create Date: 2026-10-01 10:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0006_phase7_dashboard_versioning'
down_revision: Union[str, None] = '0005_phase6_career_learning'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add version column to resumes table
    op.add_column('resumes', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.create_index('ix_resumes_version', 'resumes', ['version'])


def downgrade() -> None:
    op.drop_index('ix_resumes_version', table_name='resumes')
    op.drop_column('resumes', 'version')
