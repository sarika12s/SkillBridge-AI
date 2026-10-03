"""Resume endpoints for upload, listing, retrieval, and deletion."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.resume import (
    StructuredResumeResponse,
    ResumeSummaryResponse,
)
from app.schemas.dashboard import (
    ResumeVersionSummary,
    ResumeVersionComparisonResponse,
)
from app.schemas.skill import ResumeSkillsResponse
from app.schemas.star_guidance import ResumeSTARGuidanceResponse
from app.services.resume_service import (
    process_resume_upload,
    get_user_resumes,
    get_resume_by_id,
    delete_resume_by_id,
)
from app.services.skill_service import SkillService
from app.services.version_service import VersionService
from app.services.star_guidance_service import star_guidance_service

router = APIRouter(prefix="/resumes", tags=["Resumes"])
skill_service = SkillService()


@router.post(
    "/upload",
    response_model=StructuredResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a resume",
)
def upload_resume(
    file: UploadFile = File(..., description="PDF or DOCX resume document"),
    title: Optional[str] = Form(None, description="Optional custom title for the resume"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Accepts PDF or DOCX file, validates structure, performs OCR fallback if required,
    segments sections, extracts contact information and entities, persists records,
    and returns structured parsed resume.
    """
    user_uuid = uuid.UUID(user_id)
    return process_resume_upload(file=file, user_id=user_uuid, db=db, title=title)


@router.get(
    "",
    response_model=List[ResumeSummaryResponse],
    summary="List all uploaded resumes for current user",
)
def list_resumes(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieve all resumes owned by the authenticated candidate."""
    user_uuid = uuid.UUID(user_id)
    return get_user_resumes(user_id=user_uuid, db=db)


@router.get(
    "/versions",
    response_model=List[ResumeVersionSummary],
    summary="List all resume versions for current user",
)
def list_resume_versions(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieve chronological versions of all resumes uploaded by the authenticated candidate."""
    user_uuid = uuid.UUID(user_id)
    service = VersionService(db)
    return service.list_resume_versions(user_id=user_uuid)


@router.get(
    "/compare",
    response_model=ResumeVersionComparisonResponse,
    summary="Compare two resume versions for current user",
)
def compare_resume_versions(
    resume_id_1: uuid.UUID,
    resume_id_2: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Compare two resume versions: diffs skills, section contents, and checks score comparability guard.
    """
    user_uuid = uuid.UUID(user_id)
    service = VersionService(db)
    return service.compare_resume_versions(
        user_id=user_uuid,
        resume_id_1=resume_id_1,
        resume_id_2=resume_id_2,
    )


@router.get(
    "/{id}",
    response_model=StructuredResumeResponse,
    summary="Get full structured resume by ID",
)
def get_resume(
    id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieve full parsed resume details including all sections and extracted contact info."""
    user_uuid = uuid.UUID(user_id)
    return get_resume_by_id(resume_id=id, user_id=user_uuid, db=db)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume by ID",
)
def delete_resume(
    id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a resume and all associated sections and stored files."""
    user_uuid = uuid.UUID(user_id)
    delete_resume_by_id(resume_id=id, user_id=user_uuid, db=db)
    return None


@router.get(
    "/{id}/skills",
    response_model=ResumeSkillsResponse,
    summary="Get extracted and normalized skills for a resume",
)
def get_resume_skills(
    id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieve all normalized skills extracted from resume sections with taxonomy and evidence."""
    return skill_service.get_resume_skills(resume_id=id, db=db)


@router.get(
    "/{resume_id}/star-guidance",
    response_model=ResumeSTARGuidanceResponse,
    summary="Get STAR quality guidance for a resume",
)
def get_resume_star_guidance(
    resume_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Computes deterministic rule-based STAR structural analysis across all experience
    and project achievement bullets for the exact specified resume version.
    """
    user_uuid = uuid.UUID(user_id)
    return star_guidance_service.get_resume_star_guidance(
        db=db,
        resume_id=resume_id,
        user_id=user_uuid,
    )

