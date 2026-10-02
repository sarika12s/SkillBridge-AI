"""API Router for Resume-to-Job Matching, Skill Gap Analysis, and Explainable Scores."""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.matching import (
    MatchRequestSchema,
    MatchAnalysisResponse,
    ResumeSkillGapsResponse,
    SimulationRequest,
    SimulationResponse,
)
from app.services.matching_service import matching_service
from app.services.simulation_service import simulation_service

router = APIRouter(tags=["Matching & Skill Gaps"])


@router.post(
    "/matching/analyze",
    response_model=MatchAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute comprehensive resume-to-job match analysis",
)
def analyze_match(
    request: MatchRequestSchema,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Executes hybrid matching (exact, alias, taxonomy, dense embeddings), evaluates
    experience, education, and certifications, isolates skill gaps, and calculates
    SkillBridge ATS Readiness and Job Compatibility scores.
    """
    return matching_service.analyze_match(
        db=db,
        user_id=uuid.UUID(current_user_id),
        resume_id=request.resume_id,
        job_id=request.job_id,
    )


@router.get(
    "/matching/{analysis_id}",
    response_model=MatchAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve previously stored match analysis",
)
def get_match_analysis(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Retrieves full stored breakdown and explainability report by analysis ID."""
    return matching_service.get_analysis_by_id(
        db=db,
        analysis_id=analysis_id,
        user_id=uuid.UUID(current_user_id),
    )


@router.get(
    "/resumes/{resume_id}/jobs/{job_id}/match",
    response_model=MatchAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get or compute match between a specific resume and job",
)
def get_resume_job_match(
    resume_id: uuid.UUID,
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Fetches latest analysis for resume and job, or executes analysis if not present."""
    return matching_service.get_or_create_match(
        db=db,
        user_id=uuid.UUID(current_user_id),
        resume_id=resume_id,
        job_id=job_id,
    )


@router.get(
    "/resumes/{resume_id}/skill-gaps",
    response_model=ResumeSkillGapsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve prioritized skill gaps for a resume",
)
def get_resume_skill_gaps(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Returns prioritized required and preferred skill gaps for targeted learning."""
    return matching_service.get_resume_skill_gaps(
        db=db,
        resume_id=resume_id,
        user_id=uuid.UUID(current_user_id),
    )


@router.post(
    "/matching/simulate",
    response_model=SimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute interactive What-If gap-closure simulation",
)
def simulate_match(
    request: SimulationRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Simulates counterfactual acquisition of candidate skill gaps for a previously stored
    match analysis. Recalculates ATS Readiness and Job Compatibility scores deterministically
    via the Phase 5 ScoringEngine with zero database persistence.
    """
    return simulation_service.simulate_gap_closure(
        db=db,
        user_id=uuid.UUID(current_user_id),
        match_analysis_id=request.match_analysis_id,
        simulated_skill_ids=request.simulated_skill_ids,
    )
