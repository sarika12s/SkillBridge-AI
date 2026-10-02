"""Phase 5 schema for match analyses, skill matches, skill gaps, and score breakdowns

Revision ID: 0004_phase5_matching_tables
Revises: 0003_phase4_job_tables
Create Date: 2026-09-30 21:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0004_phase5_matching_tables'
down_revision: Union[str, None] = '0003_phase4_job_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. match_analyses table
    op.create_table(
        'match_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('compatibility_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ats_readiness_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('matching_engine_version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('scoring_version', sa.String(50), nullable=False, server_default='1.0.0-heuristic'),
        sa.Column('embedding_model', sa.String(100), nullable=False, server_default='sentence-transformers/all-MiniLM-L6-v2'),
        sa.Column('taxonomy_versions', sa.String(100), nullable=False, server_default='ESCO-v1.2,ONET-v28.0'),
        sa.Column('summary_explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_match_analyses_user_id', 'match_analyses', ['user_id'])
    op.create_index('ix_match_analyses_resume_id', 'match_analyses', ['resume_id'])
    op.create_index('ix_match_analyses_job_id', 'match_analyses', ['job_id'])

    # 2. skill_matches table
    op.create_table(
        'skill_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('match_analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('match_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_skills.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resume_skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_skills.id', ondelete='SET NULL'), nullable=True),
        sa.Column('canonical_skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='SET NULL'), nullable=True),
        sa.Column('canonical_skill_name', sa.String(255), nullable=False),
        sa.Column('match_type', sa.String(50), nullable=False),
        sa.Column('match_status', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(50), nullable=False, server_default='REQUIRED'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('resume_evidence', sa.Text(), nullable=True),
        sa.Column('job_evidence', sa.Text(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_skill_matches_analysis_id', 'skill_matches', ['match_analysis_id'])
    op.create_index('ix_skill_matches_job_skill_id', 'skill_matches', ['job_skill_id'])
    op.create_index('ix_skill_matches_resume_skill_id', 'skill_matches', ['resume_skill_id'])
    op.create_index('ix_skill_matches_canonical_id', 'skill_matches', ['canonical_skill_id'])

    # 3. skill_gaps table
    op.create_table(
        'skill_gaps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('match_analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('match_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('canonical_skill_name', sa.String(255), nullable=False),
        sa.Column('priority', sa.String(50), nullable=False, server_default='REQUIRED'),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('importance_weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('job_evidence', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_skill_gaps_analysis_id', 'skill_gaps', ['match_analysis_id'])

    # 4. score_breakdowns table
    op.create_table(
        'score_breakdowns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('match_analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('match_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('component_name', sa.String(100), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('max_possible', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('weighted_score', sa.Float(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_score_breakdowns_analysis_id', 'score_breakdowns', ['match_analysis_id'])


def downgrade() -> None:
    op.drop_table('score_breakdowns')
    op.drop_table('skill_gaps')
    op.drop_table('skill_matches')
    op.drop_table('match_analyses')
