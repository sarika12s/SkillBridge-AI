"""Job Description endpoints for ingestion, listing, retrieval, and deletion."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.job import (
    JobCreatePastedSchema,
    JobSummaryResponse,
    StructuredJobResponse,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Job Descriptions"])
job_service = JobService()


@router.post(
    "",
    response_model=StructuredJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest and analyze pasted job description text",
)
def create_job_pasted(
    payload: JobCreatePastedSchema,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Accepts pasted job description text, detects sections, classifies canonical role,
    extracts requirements, normalizes skills to ESCO/O*NET, and returns structured job profile.
    """
    user_uuid = uuid.UUID(user_id)
    return job_service.create_job_from_pasted_text(data=payload, user_id=user_uuid, db=db)


@router.post(
    "/upload",
    response_model=StructuredJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and analyze a PDF or DOCX job description",
)
def upload_job_file(
    file: UploadFile = File(..., description="PDF or DOCX job description file"),
    title: Optional[str] = Form(None, description="Optional job title"),
    company: Optional[str] = Form(None, description="Optional hiring company"),
    location: Optional[str] = Form(None, description="Optional job location"),
    source_url: Optional[str] = Form(None, description="Optional source job post URL"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Accepts PDF or DOCX job description document, extracts text, segments sections,
    extracts requirements and skills, and persists structured job representation.
    """
    user_uuid = uuid.UUID(user_id)
    return job_service.create_job_from_file_upload(
        file=file,
        title=title or file.filename or "Job Description",
        user_id=user_uuid,
        db=db,
        company=company,
        location=location,
        source_url=source_url,
    )


@router.get(
    "",
    response_model=List[JobSummaryResponse],
    summary="List all ingested job descriptions for the authenticated user",
)
def list_jobs(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieves summaries of all job descriptions ingested by current user."""
    user_uuid = uuid.UUID(user_id)
    return job_service.get_user_jobs(user_id=user_uuid, db=db)


@router.get(
    "/{id}",
    response_model=StructuredJobResponse,
    summary="Get full structured job profile by ID",
)
def get_job(
    id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieves complete structured job profile with requirements and canonical skills."""
    user_uuid = uuid.UUID(user_id)
    return job_service.get_job_by_id(job_id=id, user_id=user_uuid, db=db)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job description by ID",
)
def delete_job(
    id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Deletes job description and cascades all associated requirements and skills."""
    user_uuid = uuid.UUID(user_id)
    job_service.delete_job_by_id(job_id=id, user_id=user_uuid, db=db)
    return None
