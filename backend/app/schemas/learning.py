"""Pydantic v2 schemas for Learning Resources, Learning Paths, Stages, and DAG Visualization."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class LearningResourceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    skill_id: uuid.UUID
    skill_name: Optional[str] = None
    title: str
    provider: str
    url: str
    resource_type: str = Field("DOCUMENTATION", description="DOCUMENTATION, COURSE, TUTORIAL, BOOK, INTERACTIVE")
    cost_type: str = Field("FREE", description="FREE, PAID, FREEMIUM")
    difficulty_level: str = Field("BEGINNER", description="BEGINNER, INTERMEDIATE, ADVANCED")
    estimated_hours: float = 5.0
    description: Optional[str] = None
    rating: float = 4.8


class LearningPathItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    learning_path_id: Optional[uuid.UUID] = None
    skill_id: uuid.UUID
    skill_name: str
    skill_category: Optional[str] = None
    stage_order: int = 1
    sequence_in_stage: int = 1
    status: str = Field("NOT_STARTED", description="NOT_STARTED, IN_PROGRESS, COMPLETED")
    estimated_hours: float = 5.0
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    prerequisites_summary: Optional[str] = None
    resource: Optional[LearningResourceSchema] = None


class LearningStageSchema(BaseModel):
    stage_number: int
    stage_title: str
    stage_description: str
    stage_estimated_hours: float
    items: List[LearningPathItemSchema] = Field(default_factory=list)


class LearningPathGraphNode(BaseModel):
    id: str
    label: str
    status: str  # ACQUIRED, NOT_STARTED, IN_PROGRESS, COMPLETED
    category: Optional[str] = None
    stage: int = 1


class LearningPathGraphEdge(BaseModel):
    source: str
    target: str
    relationship_type: str = "PREREQUISITE_OF"


class LearningPathGraphSchema(BaseModel):
    nodes: List[LearningPathGraphNode] = Field(default_factory=list)
    edges: List[LearningPathGraphEdge] = Field(default_factory=list)


class LearningPathCreateRequest(BaseModel):
    resume_id: uuid.UUID
    target_type: str = Field(..., description="CAREER or JOB")
    target_occupation_id: Optional[uuid.UUID] = None
    target_job_id: Optional[uuid.UUID] = None


class ItemProgressUpdateRequest(BaseModel):
    status: str = Field(..., description="NOT_STARTED, IN_PROGRESS, COMPLETED")
    notes: Optional[str] = None


class LearningPathResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    resume_id: uuid.UUID
    target_type: str
    target_occupation_id: Optional[uuid.UUID] = None
    target_job_id: Optional[uuid.UUID] = None
    target_title: Optional[str] = None
    title: str
    description: Optional[str] = None
    total_estimated_hours_min: int = 0
    total_estimated_hours_max: int = 0
    status: str = "IN_PROGRESS"
    overall_progress_percentage: float = 0.0
    stages: List[LearningStageSchema] = Field(default_factory=list)
    graph: Optional[LearningPathGraphSchema] = None
    created_at: datetime
    updated_at: datetime
