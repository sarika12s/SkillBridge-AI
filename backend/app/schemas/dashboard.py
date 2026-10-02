"""Pydantic v2 schemas for Career Intelligence Dashboard, Version Tracking, and Analytics."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.resume import ResumeSummaryResponse


class ResumeVersionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    title: str
    file_name: str
    file_type: str
    file_size_bytes: int
    parsing_status: str
    skills_count: int = 0
    created_at: datetime
    last_analysis_at: Optional[datetime] = None


class ResumeVersionComparisonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resume_v1_id: uuid.UUID
    resume_v1_version: int
    resume_v1_title: str
    resume_v1_created_at: datetime

    resume_v2_id: uuid.UUID
    resume_v2_version: int
    resume_v2_title: str
    resume_v2_created_at: datetime

    new_skills: List[str] = Field(default_factory=list)
    retained_skills: List[str] = Field(default_factory=list)
    removed_skills: List[str] = Field(default_factory=list)

    skill_evidence_changes: List[Dict[str, Any]] = Field(default_factory=list)
    section_changes: Dict[str, Any] = Field(default_factory=dict)

    # Score comparability guard
    ats_score_v1: Optional[float] = None
    ats_score_v2: Optional[float] = None
    ats_score_delta: Optional[float] = None

    job_compatibility_v1: Optional[float] = None
    job_compatibility_v2: Optional[float] = None
    job_compatibility_delta: Optional[float] = None

    is_same_job_comparison: bool = False
    target_job_title: Optional[str] = None
    comparability_notes: str = ""


class SkillHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resume_id: uuid.UUID
    resume_version: int
    detected_at: datetime
    status: str = Field(
        ...,
        description="FIRST_DETECTED, RETAINED, NEW, REMOVED, STRENGTHENED, WEAKENED, UNKNOWN",
    )
    evidence_sentence: Optional[str] = None
    source_section: Optional[str] = None
    confidence: float = 1.0


class SkillHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_name: str
    category: str
    current_status: str
    history: List[SkillHistoryItem] = Field(default_factory=list)


class ScoreHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    analysis_id: uuid.UUID
    analysis_type: str = "JOB_MATCH"  # JOB_MATCH or CAREER_COMPATIBILITY
    resume_id: uuid.UUID
    resume_version: int
    target_id: uuid.UUID
    target_title: str
    company_name: Optional[str] = None
    ats_readiness_score: Optional[float] = None
    compatibility_score: float
    required_skill_coverage: Optional[float] = None
    preferred_skill_coverage: Optional[float] = None
    scoring_version: str = "1.0.0-heuristic"
    engine_version: str = "1.0.0"
    created_at: datetime


class LearningProgressOverview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_paths: int = 0
    completed_paths: int = 0
    in_progress_paths: int = 0
    active_path_id: Optional[uuid.UUID] = None
    active_path_title: Optional[str] = None
    active_path_target: Optional[str] = None
    total_items: int = 0
    completed_items: int = 0
    in_progress_items: int = 0
    not_started_items: int = 0
    overall_completion_percentage: float = 0.0
    total_estimated_hours: float = 0.0
    remaining_estimated_hours: float = 0.0
    current_stage: int = 1


class DashboardOverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    state: str = Field(
        ...,
        description="NEW_USER, NO_RESUME, RESUME_ONLY, RESUME_ANALYZED, JOB_ANALYZED, CAREER_ANALYZED, LEARNING_PATH_CREATED, ACTIVE_LEARNING, COMPLETED_LEARNING",
    )
    latest_resume: Optional[ResumeSummaryResponse] = None
    resume_versions_count: int = 0
    latest_job_analysis: Optional[Dict[str, Any]] = None

    # Analytical metrics (Backend is source of truth)
    latest_ats_readiness_score: Optional[float] = None
    latest_job_compatibility_score: Optional[float] = None
    required_skill_coverage: Optional[float] = None
    preferred_skill_coverage: Optional[float] = None

    matched_skills_count: int = 0
    missing_required_skills_count: int = 0
    missing_preferred_skills_count: int = 0

    top_career_roles: List[Dict[str, Any]] = Field(default_factory=list)
    learning_overview: Optional[LearningProgressOverview] = None
    score_trends: List[ScoreHistoryItem] = Field(default_factory=list)
    skill_gap_trends: List[Dict[str, Any]] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
