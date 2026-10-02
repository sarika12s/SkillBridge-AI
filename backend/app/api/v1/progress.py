"""API endpoints for skill progression, learning progress, and score history."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.dashboard import (
    SkillHistoryResponse,
    LearningProgressOverview,
    ScoreHistoryItem,
)
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["Progress Tracking"])


@router.get(
    "/skills",
    response_model=List[SkillHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user skill evolution history across resume versions",
)
def get_skill_history(
    skill_name: Optional[str] = Query(None, description="Filter for specific skill name"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Returns historical progression of skills across chronological resume versions.
    Classifies skills as FIRST_DETECTED, RETAINED, NEW, REMOVED, STRENGTHENED, or WEAKENED.
    """
    user_uuid = uuid.UUID(user_id)
    service = ProgressService(db)
    return service.get_skill_history(user_id=user_uuid, skill_name=skill_name)


@router.get(
    "/learning",
    response_model=LearningProgressOverview,
    status_code=status.HTTP_200_OK,
    summary="Get user personalized learning path progress metrics",
)
def get_learning_progress(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Returns learning path progress, completed vs remaining hours, and current stage.
    """
    user_uuid = uuid.UUID(user_id)
    service = ProgressService(db)
    return service.get_learning_progress(user_id=user_uuid)


@router.get(
    "/scores",
    response_model=List[ScoreHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Get chronological score history for job matching and career compatibility",
)
def get_score_history(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Returns chronological score progression across resume versions and job/career analyses.
    """
    user_uuid = uuid.UUID(user_id)
    service = ProgressService(db)
    return service.get_score_history(user_id=user_uuid)
