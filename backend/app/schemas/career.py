"""Pydantic v2 schemas for Career Roles, Occupations, and Career Compatibility."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class OccupationSkillSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    skill_id: uuid.UUID
    skill_name: Optional[str] = None
    requirement_type: str = Field("REQUIRED", description="REQUIRED, PREFERRED")
    importance_weight: float = Field(1.0, ge=0.0)


class OccupationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    normalized_title: str
    description: str
    category: str
    source: str
    source_version: str
    created_at: Optional[datetime] = None
    skills: List[OccupationSkillSchema] = Field(default_factory=list)


class CareerCompatibilityComponentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    component_name: str
    score: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    weighted_score: float = Field(..., ge=0.0, le=100.0)
    explanation: str


class CareerRoleMatchSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    occupation_id: uuid.UUID
    occupation_title: str
    occupation_code: str
    category: str
    compatibility_score: float = Field(..., ge=0.0, le=100.0)
    summary_explanation: str
    components: List[CareerCompatibilityComponentSchema] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    skill_gaps: List[str] = Field(default_factory=list)
    matched_skills_count: int
    total_skills_count: int


class CareerCompatibilityResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resume_id: uuid.UUID
    roles: List[CareerRoleMatchSchema] = Field(default_factory=list)
    matching_engine_version: str = "1.0.0"
    scoring_version: str = "1.0.0-heuristic"
