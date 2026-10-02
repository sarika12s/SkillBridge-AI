"""SQLAlchemy models for canonical skills, aliases, relationships, and resume skill mentions."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    normalized_name: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(100), default="TECHNICAL_SKILL", nullable=False
    )  # 'PROGRAMMING_LANGUAGE', 'FRAMEWORK', 'DATABASE', 'CLOUD_DEVOPS', 'AI_ML', etc.
    taxonomy_source: Mapped[str] = mapped_column(
        String(50), default="CUSTOM", nullable=False
    )  # 'ESCO', 'ONET', 'CUSTOM', 'HYBRID'
    taxonomy_code: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    aliases: Mapped[List["SkillAlias"]] = relationship(
        "SkillAlias", back_populates="skill", cascade="all, delete-orphan"
    )
    source_relationships: Mapped[List["SkillRelationship"]] = relationship(
        "SkillRelationship",
        foreign_keys="SkillRelationship.source_skill_id",
        back_populates="source_skill",
        cascade="all, delete-orphan",
    )
    target_relationships: Mapped[List["SkillRelationship"]] = relationship(
        "SkillRelationship",
        foreign_keys="SkillRelationship.target_skill_id",
        back_populates="target_skill",
        cascade="all, delete-orphan",
    )
    resume_mentions: Mapped[List["ResumeSkill"]] = relationship(
        "ResumeSkill", back_populates="skill"
    )


class SkillAlias(Base):
    __tablename__ = "skill_aliases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    alias_type: Mapped[str] = mapped_column(
        String(50), default="SYNONYM", nullable=False
    )  # 'ACRONYM', 'SYNONYM', 'SPELLING_VARIANT', 'FRAMEWORK_SUBSET'
    source: Mapped[str] = mapped_column(
        String(100), default="CURATED_TECH_DICT", nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    skill: Mapped["Skill"] = relationship("Skill", back_populates="aliases")


class SkillRelationship(Base):
    __tablename__ = "skill_relationships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'PREREQUISITE_OF', 'RELATED_TO', 'SUBSKILL_OF', 'PART_OF', 'USED_WITH'
    strength_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source: Mapped[str] = mapped_column(
        String(100), default="CURATED_KNOWLEDGE_GRAPH", nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    source_skill: Mapped["Skill"] = relationship(
        "Skill", foreign_keys=[source_skill_id], back_populates="source_relationships"
    )
    target_skill: Mapped["Skill"] = relationship(
        "Skill", foreign_keys=[target_skill_id], back_populates="target_relationships"
    )


class ResumeSkill(Base):
    __tablename__ = "resume_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    raw_skill_text: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_section: Mapped[str] = mapped_column(String(50), default="SKILLS", nullable=False)
    evidence_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    match_method: Mapped[str] = mapped_column(
        String(50), default="EXACT", nullable=False
    )  # 'EXACT', 'ALIAS', 'LEXICON_MATCH', 'SEMANTIC_EMBEDDING'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    resume: Mapped["Resume"] = relationship("Resume", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="resume_mentions")
