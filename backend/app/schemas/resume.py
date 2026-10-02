"""Pydantic v2 schemas for resumes, sections, and structured responses."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PersonalInformationSchema(BaseModel):
    name: Optional[str] = Field(None, description="Candidate full name")
    email: Optional[str] = Field(None, description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    location: Optional[str] = Field(None, description="City / state / country location")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    github_url: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio_url: Optional[str] = Field(None, description="Personal portfolio or website URL")


class ResumeSectionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    section_type: str = Field(..., description="Normalized section type (e.g. SUMMARY, EDUCATION, SKILLS)")
    section_title: str = Field(..., description="Original section heading text found in the document")
    content_text: str = Field(..., description="Extracted content text of the section")
    order_index: int = Field(0, description="Sequential appearance order in document")
    confidence_score: float = Field(1.0, description="Heuristic classification confidence (0.0 - 1.0)")


class ResumeProjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    project_name: str
    role: Optional[str] = None
    description: Optional[str] = None
    technologies_used: Optional[List[str]] = None
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ResumeExperienceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    company_name: str
    job_title: str
    location: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False


class ResumeCertificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiration_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class ResumeSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    file_name: str
    file_type: str
    file_size_bytes: int
    parsing_status: str
    extraction_method: str
    page_count: int
    character_count: int
    version: int = 1
    parsed_at: Optional[datetime] = None
    created_at: datetime
    sections_count: int = 0


class StructuredResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    file_name: str
    file_type: str
    file_size_bytes: int
    parsing_status: str
    extraction_method: str
    page_count: int
    character_count: int
    version: int = 1
    parsed_at: Optional[datetime] = None
    created_at: datetime
    personal_information: PersonalInformationSchema
    sections: List[ResumeSectionSchema] = []
    experience: List[ResumeExperienceSchema] = []
    projects: List[ResumeProjectSchema] = []
    certifications: List[ResumeCertificationSchema] = []
    raw_text: Optional[str] = None
