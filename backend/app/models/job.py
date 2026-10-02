"""SQLAlchemy models for Job Descriptions, structured sections, requirements, and job skills."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, Text, ForeignKey, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_role: Mapped[str] = mapped_column(
        String(150), default="Software Engineer", nullable=False, index=True
    )
    role_confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    role_classification_method: Mapped[str] = mapped_column(
        String(50), default="RULE_BASED", nullable=False
    )
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ingestion_type: Mapped[str] = mapped_column(
        String(50), default="PASTED", nullable=False
    )  # 'PASTED', 'PDF', 'DOCX'
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    user: Mapped["User"] = relationship("User", back_populates="jobs")
    sections: Mapped[List["JobSection"]] = relationship(
        "JobSection", back_populates="job", cascade="all, delete-orphan", order_by="JobSection.order_index"
    )
    requirements: Mapped[List["JobRequirement"]] = relationship(
        "JobRequirement", back_populates="job", cascade="all, delete-orphan"
    )
    skills: Mapped[List["JobSkill"]] = relationship(
        "JobSkill", back_populates="job", cascade="all, delete-orphan"
    )
    experience_requirements: Mapped[List["JobExperienceRequirement"]] = relationship(
        "JobExperienceRequirement", back_populates="job", cascade="all, delete-orphan"
    )
    education_requirements: Mapped[List["JobEducationRequirement"]] = relationship(
        "JobEducationRequirement", back_populates="job", cascade="all, delete-orphan"
    )
    certifications: Mapped[List["JobCertification"]] = relationship(
        "JobCertification", back_populates="job", cascade="all, delete-orphan"
    )


class JobSection(Base):
    __tablename__ = "job_sections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'SUMMARY', 'RESPONSIBILITIES', 'REQUIREMENTS', 'PREFERRED', 'SKILLS', etc.
    section_title: Mapped[str] = mapped_column(String(150), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    job: Mapped["Job"] = relationship("Job", back_populates="sections")


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_category: Mapped[str] = mapped_column(
        String(50), default="OTHER", nullable=False
    )  # 'SKILL', 'EXPERIENCE', 'EDUCATION', 'CERTIFICATION', 'RESPONSIBILITY', 'DOMAIN_KNOWLEDGE', 'SOFT_SKILL', 'LANGUAGE', 'OTHER'
    priority: Mapped[str] = mapped_column(
        String(50), default="UNKNOWN", nullable=False
    )  # 'REQUIRED', 'PREFERRED', 'UNKNOWN'
    source_section: Mapped[str] = mapped_column(String(100), default="REQUIREMENTS", nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    job: Mapped["Job"] = relationship("Job", back_populates="requirements")


class JobSkill(Base):
    __tablename__ = "job_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # References the SAME canonical Skill table as resumes (essential for Phase 5 matching)
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    raw_skill_text: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    requirement_type: Mapped[str] = mapped_column(
        String(50), default="UNKNOWN", nullable=False
    )  # 'REQUIRED', 'PREFERRED', 'UNKNOWN'
    source_section: Mapped[str] = mapped_column(String(100), default="REQUIREMENTS", nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    job: Mapped["Job"] = relationship("Job", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill")


class JobExperienceRequirement(Base):
    __tablename__ = "job_experience_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    minimum_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    maximum_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    experience_text: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str] = mapped_column(
        String(50), default="UNSPECIFIED", nullable=False
    )  # 'ENTRY_LEVEL', 'MID_LEVEL', 'SENIOR_LEVEL', 'EXECUTIVE', 'UNSPECIFIED'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    job: Mapped["Job"] = relationship("Job", back_populates="experience_requirements")


class JobEducationRequirement(Base):
    __tablename__ = "job_education_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    degree_level: Mapped[str] = mapped_column(
        String(100), default="UNSPECIFIED", nullable=False
    )  # 'BACHELORS', 'MASTERS', 'DOCTORATE', 'ASSOCIATE', 'DIPLOMA', 'UNSPECIFIED'
    field: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_type: Mapped[str] = mapped_column(
        String(50), default="UNKNOWN", nullable=False
    )  # 'REQUIRED', 'PREFERRED', 'UNKNOWN'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    job: Mapped["Job"] = relationship("Job", back_populates="education_requirements")


class JobCertification(Base):
    __tablename__ = "job_certifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    requirement_type: Mapped[str] = mapped_column(
        String(50), default="UNKNOWN", nullable=False
    )  # 'REQUIRED', 'PREFERRED', 'UNKNOWN'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    job: Mapped["Job"] = relationship("Job", back_populates="certifications")
