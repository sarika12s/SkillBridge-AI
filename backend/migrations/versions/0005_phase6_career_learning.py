"""Phase 6 schema for career roles, occupations, career compatibility, learning resources, and personalized learning paths

Revision ID: 0005_phase6_career_learning
Revises: 0004_phase5_matching_tables
Create Date: 2026-10-01 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0005_phase6_career_learning'
down_revision: Union[str, None] = '0004_phase5_matching_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. occupations table
    op.create_table(
        'occupations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('normalized_title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False, server_default='SOFTWARE_DEVELOPMENT'),
        sa.Column('source', sa.String(50), nullable=False, server_default='ESCO'),
        sa.Column('source_version', sa.String(50), nullable=False, server_default='v1.2'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_occupations_code', 'occupations', ['code'], unique=True)
    op.create_index('ix_occupations_title', 'occupations', ['title'])
    op.create_index('ix_occupations_normalized_title', 'occupations', ['normalized_title'])

    # 2. occupation_skills table
    op.create_table(
        'occupation_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('occupation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('occupations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_type', sa.String(50), nullable=False, server_default='REQUIRED'),
        sa.Column('importance_weight', sa.Float(), nullable=False, server_default='1.0'),
    )
    op.create_index('ix_occupation_skills_occupation_id', 'occupation_skills', ['occupation_id'])
    op.create_index('ix_occupation_skills_skill_id', 'occupation_skills', ['skill_id'])

    # 3. career_compatibilities table
    op.create_table(
        'career_compatibilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('occupation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('occupations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('compatibility_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('summary_explanation', sa.Text(), nullable=True),
        sa.Column('matching_engine_version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('scoring_version', sa.String(50), nullable=False, server_default='1.0.0-heuristic'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_career_compatibilities_user_id', 'career_compatibilities', ['user_id'])
    op.create_index('ix_career_compatibilities_resume_id', 'career_compatibilities', ['resume_id'])
    op.create_index('ix_career_compatibilities_occupation_id', 'career_compatibilities', ['occupation_id'])

    # 4. career_compatibility_components table
    op.create_table(
        'career_compatibility_components',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('career_compatibility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('career_compatibilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('component_name', sa.String(100), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('weighted_score', sa.Float(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
    )
    op.create_index('ix_career_compatibility_components_career_compatibility_id', 'career_compatibility_components', ['career_compatibility_id'])

    # 5. learning_resources table
    op.create_table(
        'learning_resources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False, server_default='DOCUMENTATION'),
        sa.Column('cost_type', sa.String(50), nullable=False, server_default='FREE'),
        sa.Column('difficulty_level', sa.String(50), nullable=False, server_default='BEGINNER'),
        sa.Column('estimated_hours', sa.Float(), nullable=False, server_default='5.0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=False, server_default='4.8'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_learning_resources_skill_id', 'learning_resources', ['skill_id'])

    # 6. learning_paths table
    op.create_table(
        'learning_paths',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_occupation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('occupations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('target_job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_estimated_hours_min', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_estimated_hours_max', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='IN_PROGRESS'),
        sa.Column('overall_progress_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_learning_paths_user_id', 'learning_paths', ['user_id'])
    op.create_index('ix_learning_paths_resume_id', 'learning_paths', ['resume_id'])
    op.create_index('ix_learning_paths_target_occupation_id', 'learning_paths', ['target_occupation_id'])
    op.create_index('ix_learning_paths_target_job_id', 'learning_paths', ['target_job_id'])

    # 7. learning_path_items table
    op.create_table(
        'learning_path_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('learning_path_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('learning_paths.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('learning_resources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('stage_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sequence_in_stage', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(50), nullable=False, server_default='NOT_STARTED'),
        sa.Column('estimated_hours', sa.Float(), nullable=False, server_default='5.0'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('prerequisites_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_learning_path_items_learning_path_id', 'learning_path_items', ['learning_path_id'])
    op.create_index('ix_learning_path_items_skill_id', 'learning_path_items', ['skill_id'])
    op.create_index('ix_learning_path_items_resource_id', 'learning_path_items', ['resource_id'])


def downgrade() -> None:
    op.drop_table('learning_path_items')
    op.drop_table('learning_paths')
    op.drop_table('learning_resources')
    op.drop_table('career_compatibility_components')
    op.drop_table('career_compatibilities')
    op.drop_table('occupation_skills')
    op.drop_table('occupations')
