"""Pydantic v2 schemas for Resume-to-Job Matching, Skill Gap Analysis, and Explainable Scores."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class MatchRequestSchema(BaseModel):
    resume_id: uuid.UUID = Field(..., description="ID of the parsed Resume")
    job_id: uuid.UUID = Field(..., description="ID of the parsed Job Description")


class SkillMatchSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    canonical_skill_name: str
    canonical_skill_id: Optional[uuid.UUID] = None
    job_skill_id: Optional[uuid.UUID] = None
    resume_skill_id: Optional[uuid.UUID] = None
    match_type: str = Field(
        ...,
        description="DIRECT_MATCH, ALIAS_MATCH, TAXONOMY_EQUIVALENT, SEMANTIC_MATCH, RELATED_SUPPORT, PARTIAL_MATCH, NO_MATCH, UNCERTAIN",
    )
    match_status: str = Field(
        ...,
        description="MATCHED_REQUIRED, MISSING_REQUIRED, PARTIAL_REQUIRED, MATCHED_PREFERRED, MISSING_PREFERRED, PARTIAL_PREFERRED, RELATED_SUPPORT, UNCERTAIN",
    )
    priority: str = Field("REQUIRED", description="REQUIRED, PREFERRED, UNKNOWN")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    similarity_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    resume_evidence: Optional[str] = None
    job_evidence: Optional[str] = None
    explanation: str


class SkillGapSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    canonical_skill_name: str
    priority: str = Field("REQUIRED", description="REQUIRED, PREFERRED, UNKNOWN")
    status: str = Field(
        ...,
        description="MISSING_REQUIRED, MISSING_PREFERRED, PARTIAL_REQUIRED, PARTIAL_PREFERRED, UNCERTAIN",
    )
    importance_weight: float = Field(1.0, ge=0.0)
    explanation: str
    job_evidence: Optional[str] = None


class ScoreBreakdownSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    component_name: str
    score: float = Field(..., ge=0.0, le=100.0)
    max_possible: float = Field(100.0, ge=0.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    weighted_score: float = Field(..., ge=0.0, le=100.0)
    explanation: str


class StructuredAlignmentSchema(BaseModel):
    experience_status: str = Field(..., description="MEETS, BELOW_REQUIREMENT, UNKNOWN")
    experience_explanation: str
    resume_years: Optional[float] = None
    required_years: Optional[float] = None

    education_status: str = Field(..., description="MEETS, PARTIAL, MISSING, UNKNOWN")
    education_explanation: str
    resume_degree: Optional[str] = None
    required_degree: Optional[str] = None

    certification_status: str = Field(..., description="MATCHED, MISSING, PARTIAL, UNKNOWN")
    certification_explanation: str
    matched_certifications: List[str] = Field(default_factory=list)
    missing_certifications: List[str] = Field(default_factory=list)


class ExplainabilitySummarySchema(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    critical_gaps: List[str] = Field(default_factory=list)
    positive_factors: List[str] = Field(default_factory=list)
    negative_factors: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)


class MatchAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    resume_id: uuid.UUID
    job_id: uuid.UUID
    job_title: str
    job_company: Optional[str] = None
    compatibility_score: float = Field(..., ge=0.0, le=100.0)
    ats_readiness_score: float = Field(..., ge=0.0, le=100.0)
    matching_engine_version: str
    scoring_version: str
    embedding_model: str
    taxonomy_versions: str
    summary_explanation: Optional[str] = None
    created_at: datetime

    skill_matches: List[SkillMatchSchema] = Field(default_factory=list)
    skill_gaps: List[SkillGapSchema] = Field(default_factory=list)
    score_breakdowns: List[ScoreBreakdownSchema] = Field(default_factory=list)
    alignment: StructuredAlignmentSchema
    explainability: ExplainabilitySummarySchema


class ResumeSkillGapsResponse(BaseModel):
    resume_id: uuid.UUID
    total_gaps: int
    required_gaps: List[SkillGapSchema] = Field(default_factory=list)
    preferred_gaps: List[SkillGapSchema] = Field(default_factory=list)


class SimulationRequest(BaseModel):
    match_analysis_id: uuid.UUID = Field(..., description="ID of the stored match analysis to simulate")
    simulated_skill_ids: List[uuid.UUID] = Field(
        ..., min_length=1, description="List of taxonomy skill IDs from current gaps to hypothetically acquire"
    )


class SimulatedSkillDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: uuid.UUID
    canonical_skill_name: str
    priority: str = Field("REQUIRED", description="REQUIRED or PREFERRED")
    current_status: str = Field(
        ...,
        description="MISSING_REQUIRED, PARTIAL_REQUIRED, MISSING_PREFERRED, PARTIAL_PREFERRED, RELATED_SUPPORT",
    )
    gap_reason: str
    estimated_learning_hours: Optional[float] = None
    learning_resources_count: int = 0


class ProjectedGapState(BaseModel):
    closed_gaps: List[str] = Field(default_factory=list, description="Skill names of gaps that would be closed")
    remaining_required_gaps: List[str] = Field(default_factory=list)
    remaining_preferred_gaps: List[str] = Field(default_factory=list)
    total_initial_gaps: int
    total_remaining_gaps: int


class CareerRoleProjection(BaseModel):
    occupation_id: uuid.UUID
    occupation_title: str
    current_compatibility_score: float = Field(..., ge=0.0, le=100.0)
    projected_compatibility_score: float = Field(..., ge=0.0, le=100.0)
    compatibility_score_delta: float


class SimulationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_analysis_id: uuid.UUID
    job_id: uuid.UUID
    job_title: str
    resume_id: uuid.UUID

    # ATS Score
    current_ats_score: float = Field(..., ge=0.0, le=100.0)
    projected_ats_score: float = Field(..., ge=0.0, le=100.0)
    ats_score_delta: float

    # Job Compatibility Score
    current_compatibility_score: float = Field(..., ge=0.0, le=100.0)
    projected_compatibility_score: float = Field(..., ge=0.0, le=100.0)
    compatibility_score_delta: float

    # Required Skill Coverage
    current_required_coverage: float = Field(..., ge=0.0, le=100.0)
    projected_required_coverage: float = Field(..., ge=0.0, le=100.0)
    required_coverage_delta: float

    # Preferred Skill Coverage
    current_preferred_coverage: float = Field(..., ge=0.0, le=100.0)
    projected_preferred_coverage: float = Field(..., ge=0.0, le=100.0)
    preferred_coverage_delta: float

    # Simulated Skills
    simulated_skills: List[SimulatedSkillDetail] = Field(default_factory=list)

    # Gap State
    gap_state: ProjectedGapState

    # Score Breakdowns (projected)
    projected_score_breakdowns: List[ScoreBreakdownSchema] = Field(default_factory=list)

    # Learning-Hour ROI
    total_estimated_learning_hours: Optional[float] = None
    learning_hour_roi: Optional[float] = None

    # Explanation Narrative
    explanation: str

    # Optional Target Role Projection
    target_role_projection: Optional[CareerRoleProjection] = None
