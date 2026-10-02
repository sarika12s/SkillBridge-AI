"""Resume service orchestrating upload, ingestion, section segmentation, and persistence."""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationException, NotFoundException
from app.models.resume import (
    Resume,
    ResumeSection,
    ResumeProject,
    ResumeExperience,
    ResumeCertification,
)
from app.schemas.resume import (
    PersonalInformationSchema,
    ResumeSectionSchema,
    ResumeProjectSchema,
    ResumeExperienceSchema,
    ResumeCertificationSchema,
    StructuredResumeResponse,
    ResumeSummaryResponse,
)
from app.ai.ingestion.validator import (
    validate_file_metadata,
    validate_file_bytes,
    generate_secure_storage_path,
)
from app.ai.ingestion.pdf_parser import parse_pdf_document
from app.ai.ingestion.docx_parser import parse_docx_document
from app.ai.segmentation.section_classifier import segment_resume_sections
from app.ai.segmentation.entity_extractor import (
    extract_contact_information,
    extract_structured_experience,
    extract_structured_projects,
    extract_structured_certifications,
)

logger = logging.getLogger(__name__)


def process_resume_upload(
    file: UploadFile,
    user_id: uuid.UUID,
    db: Session,
    title: Optional[str] = None,
) -> StructuredResumeResponse:
    """
    Complete end-to-end pipeline:
    Validate -> Securely Store -> Extract -> Segment -> Extract Entities -> Persist -> Return.
    """
    safe_name, ext = validate_file_metadata(file)

    # Read binary content into memory for validation
    file_bytes = file.file.read()
    file_size = len(file_bytes)
    validate_file_bytes(file_bytes[:16], file_size, ext)

    # Save to safe destination
    stored_filename, destination_path = generate_secure_storage_path(ext)
    try:
        with open(destination_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        logger.error(f"Failed to write file to disk: {str(e)}")
        raise ValidationException("Internal storage error while saving uploaded resume.")

    # Execute text extraction based on file extension
    try:
        if ext == ".pdf":
            raw_text, page_count, char_count, method, _ = parse_pdf_document(destination_path)
        else:
            raw_text, page_count, char_count, method, _ = parse_docx_document(destination_path)
    except Exception as err:
        # Cleanup file if parsing completely fails
        if os.path.exists(destination_path):
            os.remove(destination_path)
        raise err

    # Perform section segmentation
    section_dicts = segment_resume_sections(raw_text)

    # Identify contact section text
    contact_text = ""
    for sec in section_dicts:
        if sec["section_type"] == "CONTACT":
            contact_text = sec["content_text"]
            break

    # Extract structured contact information
    contact_info = extract_contact_information(raw_text, contact_text)

    # Extract sub-entities
    exp_text = next((s["content_text"] for s in section_dicts if s["section_type"] == "EXPERIENCE"), "")
    proj_text = next((s["content_text"] for s in section_dicts if s["section_type"] == "PROJECTS"), "")
    cert_text = next((s["content_text"] for s in section_dicts if s["section_type"] == "CERTIFICATIONS"), "")

    parsed_exp = extract_structured_experience(exp_text)
    parsed_proj = extract_structured_projects(proj_text)
    parsed_cert = extract_structured_certifications(cert_text)

    # Persist structured resume record into database
    resume_title = title.strip() if title and title.strip() else os.path.splitext(safe_name)[0]
    now = datetime.now(timezone.utc)

    existing_versions_count = db.query(Resume).filter(Resume.user_id == user_id).count()
    version_number = existing_versions_count + 1

    resume_record = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title=resume_title,
        file_name=safe_name,
        stored_path=destination_path,
        file_type=ext.lstrip("."),
        file_size_bytes=file_size,
        parsing_status="COMPLETED",
        extraction_method=method,
        raw_text=raw_text,
        page_count=page_count,
        character_count=char_count,
        version=version_number,
        parsed_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(resume_record)

    # Persist sections
    section_models = []
    for s in section_dicts:
        sec_model = ResumeSection(
            id=uuid.uuid4(),
            resume_id=resume_record.id,
            section_type=s["section_type"],
            section_title=s["section_title"],
            content_text=s["content_text"],
            order_index=s["order_index"],
            confidence_score=s["confidence_score"],
            created_at=now,
        )
        db.add(sec_model)
        section_models.append(sec_model)

    # Persist projects
    project_models = []
    for p in parsed_proj:
        proj_model = ResumeProject(
            id=uuid.uuid4(),
            resume_id=resume_record.id,
            project_name=p["project_name"],
            role=p["role"],
            description=p["description"],
            technologies_used=p["technologies_used"],
            url=p["url"],
            start_date=p["start_date"],
            end_date=p["end_date"],
        )
        db.add(proj_model)
        project_models.append(proj_model)

    # Persist experience
    exp_models = []
    for e in parsed_exp:
        exp_model = ResumeExperience(
            id=uuid.uuid4(),
            resume_id=resume_record.id,
            company_name=e["company_name"],
            job_title=e["job_title"],
            location=e["location"],
            description=e["description"],
            start_date=e["start_date"],
            end_date=e["end_date"],
            is_current=e["is_current"],
        )
        db.add(exp_model)
        exp_models.append(exp_model)

    # Persist certifications
    cert_models = []
    for c in parsed_cert:
        cert_model = ResumeCertification(
            id=uuid.uuid4(),
            resume_id=resume_record.id,
            name=c["name"],
            issuing_organization=c["issuing_organization"],
            issue_date=c["issue_date"],
            expiration_date=c["expiration_date"],
            credential_id=c["credential_id"],
            credential_url=c["credential_url"],
        )
        db.add(cert_model)
        cert_models.append(cert_model)

    db.commit()
    db.refresh(resume_record)

    # Phase 3: Auto-extract and persist normalized skills from parsed resume sections
    try:
        from app.services.skill_service import SkillService
        skill_service = SkillService()
        skill_service.extract_and_persist_resume_skills(resume_record.id, db)
    except Exception as e:
        logger.error(f"Failed to auto-extract skills on resume upload: {str(e)}")

    # Format structured response
    return StructuredResumeResponse(
        id=resume_record.id,
        user_id=resume_record.user_id,
        title=resume_record.title,
        file_name=resume_record.file_name,
        file_type=resume_record.file_type,
        file_size_bytes=resume_record.file_size_bytes,
        parsing_status=resume_record.parsing_status,
        extraction_method=resume_record.extraction_method,
        page_count=resume_record.page_count,
        character_count=resume_record.character_count,
        parsed_at=resume_record.parsed_at,
        created_at=resume_record.created_at,
        personal_information=PersonalInformationSchema(**contact_info),
        sections=[ResumeSectionSchema.model_validate(s) for s in section_models],
        experience=[ResumeExperienceSchema.model_validate(e) for e in exp_models],
        projects=[ResumeProjectSchema.model_validate(p) for p in project_models],
        certifications=[ResumeCertificationSchema.model_validate(c) for c in cert_models],
        raw_text=raw_text,
    )


def get_user_resumes(user_id: uuid.UUID, db: Session) -> List[ResumeSummaryResponse]:
    """Retrieve all resumes owned by a user."""
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .all()
    )
    result = []
    for r in resumes:
        sec_count = len(r.sections) if r.sections else 0
        summary = ResumeSummaryResponse(
            id=r.id,
            user_id=r.user_id,
            title=r.title,
            file_name=r.file_name,
            file_type=r.file_type,
            file_size_bytes=r.file_size_bytes,
            parsing_status=r.parsing_status,
            extraction_method=r.extraction_method,
            page_count=r.page_count,
            character_count=r.character_count,
            parsed_at=r.parsed_at,
            created_at=r.created_at,
            sections_count=sec_count,
        )
        result.append(summary)
    return result


def get_resume_by_id(resume_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> StructuredResumeResponse:
    """Retrieve full structured resume details by ID with authorization verification."""
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == user_id)
        .first()
    )
    if not resume:
        raise NotFoundException(f"Resume with ID {resume_id} not found.")

    contact_text = ""
    for sec in resume.sections:
        if sec.section_type == "CONTACT":
            contact_text = sec.content_text
            break

    contact_info = extract_contact_information(resume.raw_text or "", contact_text)

    return StructuredResumeResponse(
        id=resume.id,
        user_id=resume.user_id,
        title=resume.title,
        file_name=resume.file_name,
        file_type=resume.file_type,
        file_size_bytes=resume.file_size_bytes,
        parsing_status=resume.parsing_status,
        extraction_method=resume.extraction_method,
        page_count=resume.page_count,
        character_count=resume.character_count,
        parsed_at=resume.parsed_at,
        created_at=resume.created_at,
        personal_information=PersonalInformationSchema(**contact_info),
        sections=[ResumeSectionSchema.model_validate(s) for s in resume.sections],
        experience=[ResumeExperienceSchema.model_validate(e) for e in resume.experience],
        projects=[ResumeProjectSchema.model_validate(p) for p in resume.projects],
        certifications=[ResumeCertificationSchema.model_validate(c) for c in resume.certifications],
        raw_text=resume.raw_text,
    )


def delete_resume_by_id(resume_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> None:
    """Delete a resume and purge its file from disk."""
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == user_id)
        .first()
    )
    if not resume:
        raise NotFoundException(f"Resume with ID {resume_id} not found.")

    # Remove file on disk if it exists
    if resume.stored_path and os.path.exists(resume.stored_path):
        try:
            os.remove(resume.stored_path)
        except OSError as e:
            logger.warning(f"Could not remove resume file {resume.stored_path}: {str(e)}")

    db.delete(resume)
    db.commit()
