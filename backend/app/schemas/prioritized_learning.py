"""Pydantic v2 schemas for Intelligent Skill Dependency & Roadmap Prioritization (Phase 8.4)."""

import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PrioritizedSkillSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: uuid.UUID
    skill_name: str
    category: str = "TECHNICAL_SKILL"
    priority_score: float = Field(..., description="Calculated priority score bounded 0.0 - 100.0")
    role_criticality: float = Field(..., description="Role Criticality (RC) 0.0 - 100.0")
    dependency_leverage: float = Field(..., description="Dependency Leverage (DL) 0.0 - 100.0")
    gap_impact: float = Field(..., description="Gap Impact (GI) 0.0 - 100.0")
    learning_efficiency: float = Field(..., description="Learning Efficiency (LE) 0.0 - 100.0")
    readiness_status: str = Field(..., description="Readiness status: 'READY', 'BLOCKED', or 'COMPLETED'")
    unsatisfied_prerequisites: List[str] = Field(default_factory=list)
    satisfied_prerequisites: List[str] = Field(default_factory=list)
    downstream_unlocked_skills: List[str] = Field(default_factory=list)
    downstream_unlocked_count: int = 0
    estimated_hours: float = 6.0
    delta_compatibility: float = Field(0.0, description="Projected compatibility score gain from acquiring this skill")
    is_implicit_prerequisite: bool = Field(False, description="True if surfaced by dependency graph rather than explicit target mention")
    explanation: str = Field(..., description="Deterministic, student-friendly explanation of priority and readiness")
    item_id: Optional[uuid.UUID] = Field(None, description="LearningPathItem ID if present in the curriculum")
    status: str = Field("NOT_STARTED", description="Progress status: NOT_STARTED, IN_PROGRESS, COMPLETED")
    stage_order: Optional[int] = Field(None, description="Assigned stage order in curriculum if mapped")


class NextBestSkillSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: uuid.UUID
    skill_name: str
    category: str = "TECHNICAL_SKILL"
    priority_score: float
    estimated_hours: float = 6.0
    delta_compatibility: float = 0.0
    downstream_unlocked_count: int = 0
    downstream_unlocked_skills: List[str] = Field(default_factory=list)
    explanation: str
    is_implicit_prerequisite: bool = False
    item_id: Optional[uuid.UUID] = None


class DiagnosticCycleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    has_cycle: bool = False
    cycle_paths: List[List[str]] = Field(default_factory=list)


class PrioritizedRoadmapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    learning_path_id: uuid.UUID
    target_type: str = Field(..., description="'CAREER' or 'JOB'")
    target_title: Optional[str] = None
    overall_progress_percentage: float = 0.0
    total_skills_count: int = 0
    ready_skills_count: int = 0
    blocked_skills_count: int = 0
    completed_skills_count: int = 0
    next_best_skill: Optional[NextBestSkillSchema] = None
    prioritized_skills: List[PrioritizedSkillSchema] = Field(default_factory=list)
    diagnostics: DiagnosticCycleSchema = Field(default_factory=DiagnosticCycleSchema)
