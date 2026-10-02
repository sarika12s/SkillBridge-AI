"""SQLAlchemy declarative models for Resume-to-Job Matching, Skill Gap Analysis, and Explainable Scores."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MatchAnalysis(Base):
    __tablename__ = "match_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Core Explainable Scores (Bounded 0.0 - 100.0)
    compatibility_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ats_readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Versioning & Reproducibility Metadata
    matching_engine_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(50), default="1.0.0-heuristic", nullable=False)
    embedding_model: Mapped[str] = mapped_column(
        String(100), default="sentence-transformers/all-MiniLM-L6-v2", nullable=False
    )
    taxonomy_versions: Mapped[str] = mapped_column(
        String(100), default="ESCO-v1.2,ONET-v28.0", nullable=False
    )

    # Summary Narrative
    summary_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    resume = relationship("Resume", backref="matches")
    job = relationship("Job", backref="matches")
    user = relationship("User", backref="match_analyses")

    skill_matches: Mapped[List["SkillMatch"]] = relationship(
        "SkillMatch", back_populates="analysis", cascade="all, delete-orphan"
    )
    skill_gaps: Mapped[List["SkillGap"]] = relationship(
        "SkillGap", back_populates="analysis", cascade="all, delete-orphan"
    )
    score_breakdowns: Mapped[List["ScoreBreakdown"]] = relationship(
        "ScoreBreakdown", back_populates="analysis", cascade="all, delete-orphan"
    )


class SkillMatch(Base):
    __tablename__ = "skill_matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_skills.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resume_skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_skills.id", ondelete="SET NULL"), nullable=True, index=True
    )
    canonical_skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True
    )

    canonical_skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    match_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # DIRECT_MATCH, ALIAS_MATCH, TAXONOMY_EQUIVALENT, SEMANTIC_MATCH, RELATED_SUPPORT, PARTIAL_MATCH, NO_MATCH, UNCERTAIN
    match_status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # MATCHED_REQUIRED, MISSING_REQUIRED, PARTIAL_REQUIRED, MATCHED_PREFERRED, MISSING_PREFERRED, PARTIAL_PREFERRED, RELATED_SUPPORT, UNCERTAIN
    priority: Mapped[str] = mapped_column(String(50), default="REQUIRED", nullable=False)  # REQUIRED, PREFERRED, UNKNOWN
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Traceable evidence
    resume_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    analysis: Mapped["MatchAnalysis"] = relationship("MatchAnalysis", back_populates="skill_matches")


class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    canonical_skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="REQUIRED", nullable=False)  # REQUIRED, PREFERRED, UNKNOWN
    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # MISSING_REQUIRED, MISSING_PREFERRED, PARTIAL_REQUIRED, PARTIAL_PREFERRED, UNCERTAIN
    importance_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    job_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    analysis: Mapped["MatchAnalysis"] = relationship("MatchAnalysis", back_populates="skill_gaps")


class ScoreBreakdown(Base):
    __tablename__ = "score_breakdowns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # required_skill_coverage, preferred_skill_coverage, experience_alignment, education_alignment, certification_alignment, evidence_coverage, semantic_partial_coverage
    score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 100.0
    max_possible: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)  # Weight fraction (e.g. 0.40)
    weighted_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    analysis: Mapped["MatchAnalysis"] = relationship("MatchAnalysis", back_populates="score_breakdowns")
