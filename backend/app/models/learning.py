"""SQLAlchemy declarative models for Learning Resources, Personalized Learning Paths, and Path Items."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, Text, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    resource_type: Mapped[str] = mapped_column(
        String(50), default="DOCUMENTATION", nullable=False
    )  # DOCUMENTATION, COURSE, TUTORIAL, BOOK, INTERACTIVE
    cost_type: Mapped[str] = mapped_column(
        String(50), default="FREE", nullable=False
    )  # FREE, PAID, FREEMIUM
    difficulty_level: Mapped[str] = mapped_column(
        String(50), default="BEGINNER", nullable=False
    )  # BEGINNER, INTERMEDIATE, ADVANCED
    estimated_hours: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=4.8, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    skill = relationship("Skill", backref="learning_resources")
    path_items: Mapped[List["LearningPathItem"]] = relationship(
        "LearningPathItem", back_populates="resource"
    )


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # CAREER, JOB
    target_occupation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("occupations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_estimated_hours_min: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_estimated_hours_max: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="IN_PROGRESS", nullable=False
    )  # IN_PROGRESS, COMPLETED, ARCHIVED
    overall_progress_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", backref="learning_paths")
    resume = relationship("Resume", backref="learning_paths")
    occupation = relationship("Occupation", backref="learning_paths")
    job = relationship("Job", backref="learning_paths")

    items: Mapped[List["LearningPathItem"]] = relationship(
        "LearningPathItem",
        back_populates="learning_path",
        cascade="all, delete-orphan",
        order_by="LearningPathItem.stage_order, LearningPathItem.sequence_in_stage",
    )


class LearningPathItem(Base):
    __tablename__ = "learning_path_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    learning_path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_resources.id", ondelete="SET NULL"), nullable=True, index=True
    )

    stage_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sequence_in_stage: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="NOT_STARTED", nullable=False
    )  # NOT_STARTED, IN_PROGRESS, COMPLETED
    estimated_hours: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prerequisites_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_by_resume_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_method: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'RESUME_EVIDENCE', 'MANUAL'

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    learning_path: Mapped["LearningPath"] = relationship("LearningPath", back_populates="items")
    skill = relationship("Skill")
    resource: Mapped[Optional["LearningResource"]] = relationship("LearningResource", back_populates="path_items")
    verified_by_resume = relationship("Resume", foreign_keys=[verified_by_resume_id])
