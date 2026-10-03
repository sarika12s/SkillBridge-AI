"""Pydantic v2 schemas for Phase 8.3 STAR Resume Guidance.

Defines structural models for component-level detections, individual bullet analyses,
aggregate resume-level summary metrics, and the complete read-only guidance response.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class STARComponentDetail(BaseModel):
    """Detailed structural evidence and explanation for an individual STAR competency pillar."""
    model_config = ConfigDict(from_attributes=True)

    detected: bool = Field(..., description="Whether evidence for this STAR component was detected")
    evidence_text: Optional[str] = Field(None, description="Extracted textual evidence snippet or keyword")
    signals_detected: List[str] = Field(default_factory=list, description="Rule-based signal identifiers detected")
    explanation: str = Field(..., description="Deterministic explainability justification for detection status")


class BulletSTARAnalysis(BaseModel):
    """Comprehensive STAR completeness analysis for a single resume achievement bullet."""
    model_config = ConfigDict(from_attributes=True)

    bullet_id: str = Field(..., description="Deterministic derived identifier (e.g. {resume_id}:{section}:{parent}:{index})")
    section_type: str = Field(..., description="Section type originating the bullet ('EXPERIENCE' or 'PROJECTS')")
    parent_entry_title: str = Field(..., description="Parent entity title (e.g., job title at company, or project name)")
    raw_text: str = Field(..., description="Raw bullet statement text from the persisted resume")
    situation: STARComponentDetail = Field(..., description="Situation component evaluation")
    task: STARComponentDetail = Field(..., description="Task component evaluation")
    action: STARComponentDetail = Field(..., description="Action component evaluation")
    result: STARComponentDetail = Field(..., description="Result component evaluation")
    completeness_score: float = Field(..., description="Heuristic completeness score between 0.0 and 100.0")
    missing_components: List[str] = Field(default_factory=list, description="Ordered list of missing STAR components")
    improvement_guidance: List[str] = Field(
        default_factory=list,
        description="Deterministic actionable structural improvement suggestions in fixed order"
    )


class STARSummaryMetrics(BaseModel):
    """Aggregate quality and coverage metrics across all analyzed resume bullets."""
    model_config = ConfigDict(from_attributes=True)

    total_bullets_analyzed: int = Field(..., description="Total count of individual achievement bullets evaluated")
    bullets_with_action: int = Field(..., description="Count of bullets with Action verbs detected")
    bullets_with_result: int = Field(..., description="Count of bullets with quantifiable Result metrics detected")
    bullets_with_situation: int = Field(..., description="Count of bullets with operational Situation context detected")
    bullets_with_task: int = Field(..., description="Count of bullets with Task objective markers detected")
    overall_completeness_percentage: float = Field(
        ...,
        description="Arithmetic mean of bullet completeness scores (0.0 to 100.0)"
    )
    strong_bullets_count: int = Field(
        ...,
        description="Count of bullets meeting the strong criteria (Action + Result + score >= 65.0)"
    )
    needs_improvement_count: int = Field(
        ...,
        description="Count of bullets not meeting the strong criteria"
    )


class ResumeSTARGuidanceResponse(BaseModel):
    """Comprehensive read-only response for resume STAR guidance."""
    model_config = ConfigDict(from_attributes=True)

    resume_id: UUID = Field(..., description="Persisted resume unique identifier")
    resume_version: int = Field(..., description="Specific resume version analyzed")
    resume_title: str = Field(..., description="Title of the resume")
    summary: STARSummaryMetrics = Field(..., description="Aggregated STAR metrics across all bullets")
    bullets: List[BulletSTARAnalysis] = Field(default_factory=list, description="Per-bullet STAR structural evaluations")
    methodology: str = Field(
        default="Deterministic Rule-Based STAR Structural Analysis",
        description="Analysis methodology description"
    )
