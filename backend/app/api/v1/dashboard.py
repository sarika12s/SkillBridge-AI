"""API endpoints for Career Intelligence Dashboard overview and analytics."""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.dashboard import DashboardOverviewResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get unified Career Intelligence Dashboard overview",
)
def get_dashboard_overview(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Returns the aggregated dashboard overview for the authenticated user,
    including resume health, ATS/job compatibility metrics, career alignments,
    learning progress, score trends, and explainable insights.
    """
    service = DashboardService(db)
    return service.get_dashboard_overview(user_id=uuid.UUID(user_id))
