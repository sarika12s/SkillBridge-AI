"""Initial Phase 2 schema for users, profiles, resumes, and structured sections

Revision ID: 0001_initial_phase2_schema
Revises: 
Create Date: 2026-09-29 19:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_phase2_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(150), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='student'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('current_title', sa.String(150), nullable=True),
        sa.Column('target_role', sa.String(150), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('linkedin_url', sa.String(255), nullable=True),
        sa.Column('github_url', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_user_profiles_user_id', 'user_profiles', ['user_id'])

    # 3. resumes table
    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('stored_path', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('parsing_status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('extraction_method', sa.String(50), nullable=False, server_default='TEXT'),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('character_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parsed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_resumes_user_id', 'resumes', ['user_id'])

    # 4. resume_sections table
    op.create_table(
        'resume_sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_type', sa.String(50), nullable=False),
        sa.Column('section_title', sa.String(150), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_resume_sections_resume_id', 'resume_sections', ['resume_id'])

    # 5. resume_projects table
    op.create_table(
        'resume_projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(150), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('technologies_used', sa.JSON(), nullable=True),
        sa.Column('url', sa.String(255), nullable=True),
        sa.Column('start_date', sa.String(50), nullable=True),
        sa.Column('end_date', sa.String(50), nullable=True),
    )
    op.create_index('ix_resume_projects_resume_id', 'resume_projects', ['resume_id'])

    # 6. resume_experience table
    op.create_table(
        'resume_experience',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('job_title', sa.String(150), nullable=False),
        sa.Column('location', sa.String(150), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.String(50), nullable=True),
        sa.Column('end_date', sa.String(50), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.create_index('ix_resume_experience_resume_id', 'resume_experience', ['resume_id'])

    # 7. resume_certifications table
    op.create_table(
        'resume_certifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('issuing_organization', sa.String(255), nullable=True),
        sa.Column('issue_date', sa.String(50), nullable=True),
        sa.Column('expiration_date', sa.String(50), nullable=True),
        sa.Column('credential_id', sa.String(150), nullable=True),
        sa.Column('credential_url', sa.String(255), nullable=True),
    )
    op.create_index('ix_resume_certifications_resume_id', 'resume_certifications', ['resume_id'])


def downgrade() -> None:
    op.drop_table('resume_certifications')
    op.drop_table('resume_experience')
    op.drop_table('resume_projects')
    op.drop_table('resume_sections')
    op.drop_table('resumes')
    op.drop_table('user_profiles')
    op.drop_table('users')
