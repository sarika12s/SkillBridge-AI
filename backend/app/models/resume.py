"""SQLAlchemy models for parsed resumes and structured sections."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Float, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'pdf' or 'docx'
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    parsing_status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False
    )  # 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'
    extraction_method: Mapped[str] = mapped_column(
        String(50), default="TEXT", nullable=False
    )  # 'TEXT' or 'OCR'
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parsed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
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
    user: Mapped["User"] = relationship("User", back_populates="resumes")
    sections: Mapped[List["ResumeSection"]] = relationship(
        "ResumeSection",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeSection.order_index",
    )
    projects: Mapped[List["ResumeProject"]] = relationship(
        "ResumeProject", back_populates="resume", cascade="all, delete-orphan"
    )
    experience: Mapped[List["ResumeExperience"]] = relationship(
        "ResumeExperience", back_populates="resume", cascade="all, delete-orphan"
    )
    certifications: Mapped[List["ResumeCertification"]] = relationship(
        "ResumeCertification", back_populates="resume", cascade="all, delete-orphan"
    )
    skills: Mapped[List["ResumeSkill"]] = relationship(
        "ResumeSkill", back_populates="resume", cascade="all, delete-orphan"
    )


class ResumeSection(Base):
    __tablename__ = "resume_sections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'CONTACT', 'SUMMARY', 'EDUCATION', 'EXPERIENCE', 'PROJECTS', 'SKILLS', etc.
    section_title: Mapped[str] = mapped_column(String(150), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    resume: Mapped["Resume"] = relationship("Resume", back_populates="sections")


class ResumeProject(Base):
    __tablename__ = "resume_projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    technologies_used: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="projects")


class ResumeExperience(Base):
    __tablename__ = "resume_experience"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="experience")


class ResumeCertification(Base):
    __tablename__ = "resume_certifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuing_organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expiration_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    credential_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    credential_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="certifications")
