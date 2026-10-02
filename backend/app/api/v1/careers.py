"""API Router for Career Roles, Standardized Occupations, and Multi-Role Compatibility."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.career import (
    OccupationResponseSchema,
    CareerCompatibilityResponseSchema,
    OccupationSkillSchema,
)
from app.services.career_service import CareerService

router = APIRouter(prefix="/careers", tags=["Career Roles & Compatibility"])


@router.get(
    "/occupations",
    response_model=List[OccupationResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="List all standardized career occupations",
)
def list_occupations(db: Session = Depends(get_db)):
    """Retrieves all standardized ESCO/O*NET industry occupations and required skills."""
    service = CareerService(db)
    occupations = service.get_all_occupations()

    res = []
    for occ in occupations:
        sk_schemas = [
            OccupationSkillSchema(
                id=s.id,
                skill_id=s.skill_id,
                skill_name=s.skill.name if s.skill else None,
                requirement_type=s.requirement_type,
                importance_weight=s.importance_weight,
            )
            for s in occ.skills
        ]
        res.append(
            OccupationResponseSchema(
                id=occ.id,
                code=occ.code,
                title=occ.title,
                normalized_title=occ.normalized_title,
                description=occ.description,
                category=occ.category,
                source=occ.source,
                source_version=occ.source_version,
                created_at=occ.created_at,
                skills=sk_schemas,
            )
        )
    return res


@router.get(
    "/occupations/{occupation_id}",
    response_model=OccupationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Retrieve single occupation details",
)
def get_occupation(occupation_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieves details of a specific occupation by ID."""
    service = CareerService(db)
    occ = service.get_occupation_by_id(occupation_id)
    sk_schemas = [
        OccupationSkillSchema(
            id=s.id,
            skill_id=s.skill_id,
            skill_name=s.skill.name if s.skill else None,
            requirement_type=s.requirement_type,
            importance_weight=s.importance_weight,
        )
        for s in occ.skills
    ]
    return OccupationResponseSchema(
        id=occ.id,
        code=occ.code,
        title=occ.title,
        normalized_title=occ.normalized_title,
        description=occ.description,
        category=occ.category,
        source=occ.source,
        source_version=occ.source_version,
        created_at=occ.created_at,
        skills=sk_schemas,
    )


@router.get(
    "/compatibility/{resume_id}",
    response_model=CareerCompatibilityResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Compute career role compatibility for a resume",
)
def compute_career_compatibility(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Evaluates candidate's resume across all standardized industry roles.
    Returns ranked compatibility scores with explainable component breakdowns and factual narratives.
    """
    service = CareerService(db)
    return service.compute_compatibility_for_resume(
        resume_id=resume_id,
        user_id=uuid.UUID(current_user_id),
    )
