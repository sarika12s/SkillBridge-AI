"""API Router for Personalized Learning Paths and Modular Progress Tracking."""

import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.learning import (
    LearningPathCreateRequest,
    LearningPathResponseSchema,
    ItemProgressUpdateRequest,
    ReconciliationRequest,
    ReconciliationResponse,
)
from app.schemas.prioritized_learning import PrioritizedRoadmapResponse
from app.services.learning_service import LearningService
from app.services.prioritization_service import PrioritizationService

router = APIRouter(prefix="/learning-paths", tags=["Learning Paths & Progress Tracking"])


@router.post(
    "",
    response_model=LearningPathResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a personalized learning path",
)
def create_learning_path(
    request: LearningPathCreateRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Generates a personalized, prerequisite-aware learning roadmap targeting either
    a career occupation (CAREER mode) or a specific job description (JOB mode).
    Filters out already acquired skills and builds topological stages with real resources.
    """
    service = LearningService(db)
    return service.create_learning_path(
        user_id=uuid.UUID(current_user_id),
        req=request,
    )


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List all user learning paths",
)
def list_learning_paths(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Returns summary list of all learning paths belonging to the authenticated user."""
    service = LearningService(db)
    return service.get_user_learning_paths(user_id=uuid.UUID(current_user_id))


@router.get(
    "/{path_id}",
    response_model=LearningPathResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Retrieve detailed learning path with stages and DAG graph",
)
def get_learning_path(
    path_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Retrieves full learning path details including organized stages and interactive DAG graph."""
    service = LearningService(db)
    return service.get_learning_path(
        path_id=path_id,
        user_id=uuid.UUID(current_user_id),
    )


@router.get(
    "/{path_id}/prioritized",
    response_model=PrioritizedRoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve prioritized skill roadmap and Next Best Skill recommendation",
)
def get_prioritized_roadmap(
    path_id: uuid.UUID,
    include_implicit: bool = Query(
        True,
        description="Whether to discover and inject implicit prerequisite skills from explicit taxonomy relationships",
    ),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Computes deterministic, prerequisite-aware prioritization across target skills
    and implicit foundational prerequisites for students and freshers.
    Identifies the single Next Best Skill under a strict readiness hard gatekeeper.
    Completely compute-on-read: never mutates historical learning paths.
    """
    service = PrioritizationService(db)
    return service.get_prioritized_roadmap(
        path_id=path_id,
        user_id=uuid.UUID(current_user_id),
        include_implicit=include_implicit,
    )



@router.patch(
    "/items/{item_id}/progress",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Update learning item progress",
)
def update_item_progress(
    item_id: uuid.UUID,
    request: ItemProgressUpdateRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Updates the learning status of an individual item (NOT_STARTED, IN_PROGRESS, COMPLETED)
    and dynamically re-evaluates the overall learning path completion percentage.
    """
    service = LearningService(db)
    return service.update_item_progress(
        item_id=item_id,
        user_id=uuid.UUID(current_user_id),
        new_status=request.status,
        notes=request.notes,
    )


@router.post(
    "/{path_id}/reconcile",
    response_model=ReconciliationResponse,
    status_code=status.HTTP_200_OK,
    summary="Reconcile roadmap milestones against newer resume versions",
)
def reconcile_learning_path(
    path_id: uuid.UUID,
    request: Optional[ReconciliationRequest] = None,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Reconciles an active personalized learning path against a newer resume version.
    Automatically marks corresponding milestones as COMPLETED with authoritative provenance
    (RESUME_EVIDENCE), recalculates progress percentages and remaining hours.
    Idempotent and non-destructive: completed items are never demoted.
    """
    service = LearningService(db)
    return service.reconcile_learning_path(
        path_id=path_id,
        user_id=uuid.UUID(current_user_id),
        req=request,
    )
