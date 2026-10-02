"""SQLAlchemy declarative models for Career Roles, Occupations, and Career Compatibility."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, Text, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Occupation(Base):
    __tablename__ = "occupations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), default="SOFTWARE_DEVELOPMENT", nullable=False
    )
    source: Mapped[str] = mapped_column(String(50), default="ESCO", nullable=False)
    source_version: Mapped[str] = mapped_column(String(50), default="v1.2", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    skills: Mapped[List["OccupationSkill"]] = relationship(
        "OccupationSkill", back_populates="occupation", cascade="all, delete-orphan"
    )
    compatibilities: Mapped[List["CareerCompatibility"]] = relationship(
        "CareerCompatibility", back_populates="occupation", cascade="all, delete-orphan"
    )


class OccupationSkill(Base):
    __tablename__ = "occupation_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    occupation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("occupations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requirement_type: Mapped[str] = mapped_column(
        String(50), default="REQUIRED", nullable=False
    )  # REQUIRED, PREFERRED
    importance_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    occupation: Mapped["Occupation"] = relationship("Occupation", back_populates="skills")
    skill = relationship("Skill", backref="occupation_mentions")


class CareerCompatibility(Base):
    __tablename__ = "career_compatibilities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    occupation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("occupations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    compatibility_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    summary_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    matching_engine_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(50), default="1.0.0-heuristic", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    occupation: Mapped["Occupation"] = relationship("Occupation", back_populates="compatibilities")
    resume = relationship("Resume", backref="career_compatibilities")
    user = relationship("User", backref="career_compatibilities")

    components: Mapped[List["CareerCompatibilityComponent"]] = relationship(
        "CareerCompatibilityComponent", back_populates="compatibility", cascade="all, delete-orphan"
    )


class CareerCompatibilityComponent(Base):
    __tablename__ = "career_compatibility_components"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    career_compatibility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_compatibilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component_name: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    weighted_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    compatibility: Mapped["CareerCompatibility"] = relationship("CareerCompatibility", back_populates="components")
