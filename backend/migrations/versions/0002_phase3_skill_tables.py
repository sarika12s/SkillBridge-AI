"""Phase 3 schema for skills, aliases, relationships, and resume skill mentions

Revision ID: 0002_phase3_skill_tables
Revises: 0001_initial_phase2_schema
Create Date: 2026-09-29 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '0002_phase3_skill_tables'
down_revision: Union[str, None] = '0001_initial_phase2_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Enable pgvector extension if PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. skills table
    op.create_table(
        'skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('normalized_name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False, server_default='TECHNICAL_SKILL'),
        sa.Column('taxonomy_source', sa.String(50), nullable=False, server_default='CUSTOM'),
        sa.Column('taxonomy_code', sa.String(150), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_skills_name', 'skills', ['name'], unique=True)
    op.create_index('ix_skills_normalized_name', 'skills', ['normalized_name'])

    # 2. skill_aliases table
    op.create_table(
        'skill_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alias', sa.String(255), nullable=False),
        sa.Column('normalized_alias', sa.String(255), nullable=False),
        sa.Column('alias_type', sa.String(50), nullable=False, server_default='SYNONYM'),
        sa.Column('source', sa.String(100), nullable=False, server_default='CURATED_TECH_DICT'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_skill_aliases_skill_id', 'skill_aliases', ['skill_id'])
    op.create_index('ix_skill_aliases_alias', 'skill_aliases', ['alias'])
    op.create_index('ix_skill_aliases_normalized_alias', 'skill_aliases', ['normalized_alias'])

    # 3. skill_relationships table
    op.create_table(
        'skill_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('strength_weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('source', sa.String(100), nullable=False, server_default='CURATED_KNOWLEDGE_GRAPH'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_skill_relationships_source_skill_id', 'skill_relationships', ['source_skill_id'])
    op.create_index('ix_skill_relationships_target_skill_id', 'skill_relationships', ['target_skill_id'])

    # 4. resume_skills table
    op.create_table(
        'resume_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('raw_skill_text', sa.String(255), nullable=False),
        sa.Column('canonical_skill_name', sa.String(255), nullable=False),
        sa.Column('source_section', sa.String(50), nullable=False, server_default='SKILLS'),
        sa.Column('evidence_sentence', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('match_method', sa.String(50), nullable=False, server_default='EXACT'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_resume_skills_resume_id', 'resume_skills', ['resume_id'])
    op.create_index('ix_resume_skills_skill_id', 'resume_skills', ['skill_id'])


def downgrade() -> None:
    op.drop_table('resume_skills')
    op.drop_table('skill_relationships')
    op.drop_table('skill_aliases')
    op.drop_table('skills')
