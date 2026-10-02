"""Skill endpoints for extraction, canonical taxonomy queries, and relationship graphs."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.skill import (
    SkillSchema,
    SkillRelationshipSchema,
    ResumeSkillsResponse,
)
from app.services.skill_service import SkillService

router = APIRouter(prefix="/skills", tags=["Skills & Taxonomy"])
skill_service = SkillService()


@router.post(
    "/extract/{resume_id}",
    response_model=ResumeSkillsResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract and normalize skills from a parsed resume",
)
def extract_skills_endpoint(
    resume_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Triggers the skill extraction and normalization pipeline for the given resume.
    Identifies candidate mentions across resume sections, resolves aliases,
    maps to ESCO/O*NET taxonomies, preserves evidence sentences, and persists to DB.
    """
    return skill_service.extract_and_persist_resume_skills(resume_id=resume_id, db=db)


@router.get(
    "/resume/{resume_id}",
    response_model=ResumeSkillsResponse,
    summary="Get all extracted skills for a resume",
)
def get_resume_skills_endpoint(
    resume_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieves all normalized skills, evidence, and taxonomy metadata for a resume."""
    return skill_service.get_resume_skills(resume_id=resume_id, db=db)


@router.get(
    "/{id}",
    response_model=SkillSchema,
    summary="Get canonical skill details by ID",
)
def get_skill_by_id_endpoint(
    id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieves canonical skill details, known aliases, taxonomy source/code, and outgoing relationships."""
    return skill_service.get_skill_by_id(skill_id=id, db=db)


@router.get(
    "/{id}/relationships",
    response_model=List[SkillRelationshipSchema],
    summary="Get all ontology relationships for a skill",
)
def get_skill_relationships_endpoint(
    id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieves prerequisite, subskill, and related technology links for the specified skill."""
    return skill_service.get_skill_relationships(skill_id=id, db=db)
