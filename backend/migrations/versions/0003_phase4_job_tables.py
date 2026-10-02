"""Phase 4 schema for jobs, job sections, requirements, skills, experience, education, certifications

Revision ID: 0003_phase4_job_tables
Revises: 0002_phase3_skill_tables
Create Date: 2026-09-29 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003_phase4_job_tables'
down_revision: Union[str, None] = '0002_phase3_skill_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('normalized_role', sa.String(150), nullable=False, server_default='Software Engineer'),
        sa.Column('role_confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('role_classification_method', sa.String(50), nullable=False, server_default='RULE_BASED'),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('ingestion_type', sa.String(50), nullable=False, server_default='PASTED'),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_jobs_user_id', 'jobs', ['user_id'])
    op.create_index('ix_jobs_normalized_role', 'jobs', ['normalized_role'])

    # 2. job_sections table
    op.create_table(
        'job_sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_type', sa.String(50), nullable=False),
        sa.Column('section_title', sa.String(150), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_job_sections_job_id', 'job_sections', ['job_id'])

    # 3. job_requirements table
    op.create_table(
        'job_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('normalized_text', sa.Text(), nullable=False),
        sa.Column('requirement_category', sa.String(50), nullable=False, server_default='OTHER'),
        sa.Column('priority', sa.String(50), nullable=False, server_default='UNKNOWN'),
        sa.Column('source_section', sa.String(100), nullable=False, server_default='REQUIREMENTS'),
        sa.Column('evidence_text', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_job_requirements_job_id', 'job_requirements', ['job_id'])

    # 4. job_skills table (references the same canonical skills table as resumes)
    op.create_table(
        'job_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('raw_skill_text', sa.String(255), nullable=False),
        sa.Column('canonical_skill_name', sa.String(255), nullable=False),
        sa.Column('requirement_type', sa.String(50), nullable=False, server_default='UNKNOWN'),
        sa.Column('source_section', sa.String(100), nullable=False, server_default='REQUIREMENTS'),
        sa.Column('evidence_text', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_job_skills_job_id', 'job_skills', ['job_id'])
    op.create_index('ix_job_skills_skill_id', 'job_skills', ['skill_id'])

    # 5. job_experience_requirements table
    op.create_table(
        'job_experience_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('minimum_years', sa.Float(), nullable=True),
        sa.Column('maximum_years', sa.Float(), nullable=True),
        sa.Column('experience_text', sa.Text(), nullable=False),
        sa.Column('classification', sa.String(50), nullable=False, server_default='UNSPECIFIED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_job_experience_requirements_job_id', 'job_experience_requirements', ['job_id'])

    # 6. job_education_requirements table
    op.create_table(
        'job_education_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('degree_level', sa.String(100), nullable=False, server_default='UNSPECIFIED'),
        sa.Column('field', sa.String(255), nullable=True),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('requirement_type', sa.String(50), nullable=False, server_default='UNKNOWN'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_job_education_requirements_job_id', 'job_education_requirements', ['job_id'])

    # 7. job_certifications table
    op.create_table(
        'job_certifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('requirement_type', sa.String(50), nullable=False, server_default='UNKNOWN'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_job_certifications_job_id', 'job_certifications', ['job_id'])


def downgrade() -> None:
    op.drop_table('job_certifications')
    op.drop_table('job_education_requirements')
    op.drop_table('job_experience_requirements')
    op.drop_table('job_skills')
    op.drop_table('job_requirements')
    op.drop_table('job_sections')
    op.drop_table('jobs')
