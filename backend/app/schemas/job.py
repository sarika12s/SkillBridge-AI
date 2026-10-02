"""Pydantic v2 schemas for Job Descriptions, structured requirements, skills, and responses."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class JobSectionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    section_type: str
    section_title: str
    content_text: str
    order_index: int = 0


class JobRequirementSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    original_text: str
    normalized_text: str
    requirement_category: str  # 'SKILL', 'EXPERIENCE', 'EDUCATION', 'CERTIFICATION', 'RESPONSIBILITY', etc.
    priority: str  # 'REQUIRED', 'PREFERRED', 'UNKNOWN'
    source_section: str
    evidence_text: str
    confidence: float = 1.0


class JobSkillSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    skill_id: UUID
    raw_skill_text: str
    canonical_skill_name: str
    requirement_type: str  # 'REQUIRED', 'PREFERRED', 'UNKNOWN'
    source_section: str
    evidence_text: str
    confidence: float = 1.0
    taxonomy_sources: List[str] = []


class JobExperienceRequirementSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    minimum_years: Optional[float] = None
    maximum_years: Optional[float] = None
    experience_text: str
    classification: str = "UNSPECIFIED"


class JobEducationRequirementSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    degree_level: str
    field: Optional[str] = None
    original_text: str
    requirement_type: str = "UNKNOWN"


class JobCertificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    name: str
    requirement_type: str = "UNKNOWN"


class JobCreatePastedSchema(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    raw_text: str = Field(..., min_length=20)
    company: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = Field(None, max_length=500)


class JobSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    normalized_role: str
    company: Optional[str] = None
    location: Optional[str] = None
    ingestion_type: str
    total_skills: int = 0
    required_skills_count: int = 0
    preferred_skills_count: int = 0
    min_years_experience: Optional[float] = None
    created_at: datetime


class StructuredJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    normalized_role: str
    role_confidence: float
    role_classification_method: str
    company: Optional[str] = None
    location: Optional[str] = None
    source_url: Optional[str] = None
    ingestion_type: str
    raw_text: str
    summary: Optional[str] = None
    sections: List[JobSectionSchema] = []
    requirements: List[JobRequirementSchema] = []
    required_skills: List[JobSkillSchema] = []
    preferred_skills: List[JobSkillSchema] = []
    all_skills: List[JobSkillSchema] = []
    experience_requirements: List[JobExperienceRequirementSchema] = []
    education_requirements: List[JobEducationRequirementSchema] = []
    certifications: List[JobCertificationSchema] = []
    created_at: datetime
    updated_at: datetime
