"""API Router for Personalized Learning Paths and Modular Progress Tracking."""

import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.learning import (
    LearningPathCreateRequest,
    LearningPathResponseSchema,
    ItemProgressUpdateRequest,
)
from app.services.learning_service import LearningService

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
