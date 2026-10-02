"""Job Service orchestrating ingestion, section detection, requirement classification, and persistence."""

import os
import uuid
import logging
from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import (
    Job,
    JobSection,
    JobRequirement,
    JobSkill,
    JobExperienceRequirement,
    JobEducationRequirement,
    JobCertification,
)
from app.models.skill import Skill
from app.schemas.job import (
    JobCreatePastedSchema,
    JobSummaryResponse,
    StructuredJobResponse,
    JobSectionSchema,
    JobRequirementSchema,
    JobSkillSchema,
    JobExperienceRequirementSchema,
    JobEducationRequirementSchema,
    JobCertificationSchema,
)
from app.ai.jobs.text_cleaner import normalize_job_text
from app.ai.jobs.section_classifier import segment_job_sections
from app.ai.jobs.role_classifier import classify_job_role
from app.ai.jobs.requirement_extractor import parse_job_requirements
from app.ai.jobs.job_skill_extractor import JobSkillExtractor
from app.ai.ingestion.validator import validate_file_metadata, validate_file_bytes, generate_secure_storage_path
from app.ai.ingestion.pdf_parser import parse_pdf_document
from app.ai.ingestion.docx_parser import parse_docx_document
from app.data.seeders.seed_taxonomies import seed_taxonomies

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self):
        self.skill_extractor = JobSkillExtractor()

    def _ensure_taxonomies_seeded(self, db: Session) -> None:
        """Ensures canonical skills are present in DB."""
        if db.query(Skill).count() == 0:
            logger.info("No canonical skills found in database. Running initial seed...")
            seed_taxonomies(db, generate_embeddings=True)

    def process_and_persist_job(
        self,
        title: str,
        raw_text: str,
        ingestion_type: str,
        user_id: uuid.UUID,
        db: Session,
        company: Optional[str] = None,
        location: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> StructuredJobResponse:
        """
        Processes normalized text through the complete intelligence pipeline
        and persists structured entities.
        """
        self._ensure_taxonomies_seeded(db)

        # 1. Clean and normalize text
        cleaned_text = normalize_job_text(raw_text)
        if len(cleaned_text) < 20:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Job description text is too short or empty.",
            )

        # 2. Segment into sections
        sections = segment_job_sections(cleaned_text)

        # 3. Classify role
        summary_text = next((s["content_text"] for s in sections if s["section_type"] == "SUMMARY"), "")
        norm_role, role_conf, role_method = classify_job_role(title, summary_text)

        # 4. Extract requirements, experience, education, certifications
        parsed_data = parse_job_requirements(sections)

        # 5. Extract canonical skills (ensuring SAME canonical skill IDs as resumes)
        canonical_skills = db.query(Skill).all()
        canonical_id_map = {s.name: s.id for s in canonical_skills}
        extracted_skills = self.skill_extractor.extract_from_job_sections(sections, canonical_id_map)

        # 6. Create Job record
        job_record = Job(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title.strip(),
            normalized_role=norm_role,
            role_confidence=role_conf,
            role_classification_method=role_method,
            company=company.strip() if company else None,
            location=location.strip() if location else None,
            source_url=source_url.strip() if source_url else None,
            ingestion_type=ingestion_type,
            raw_text=cleaned_text,
            summary=summary_text if summary_text else None,
        )
        db.add(job_record)
        db.flush()

        # 7. Persist Sections
        section_models = []
        for sec in sections:
            sec_m = JobSection(
                id=uuid.uuid4(),
                job_id=job_record.id,
                section_type=sec["section_type"],
                section_title=sec["section_title"],
                content_text=sec["content_text"],
                order_index=sec["order_index"],
            )
            db.add(sec_m)
            section_models.append(sec_m)

        # 8. Persist Requirements
        req_models = []
        for req in parsed_data["requirements"]:
            req_m = JobRequirement(
                id=uuid.uuid4(),
                job_id=job_record.id,
                original_text=req["original_text"],
                normalized_text=req["normalized_text"],
                requirement_category=req["requirement_category"],
                priority=req["priority"],
                source_section=req["source_section"],
                evidence_text=req["evidence_text"],
                confidence=req["confidence"],
            )
            db.add(req_m)
            req_models.append(req_m)

        # 9. Persist Job Skills (linked to canonical Skill table)
        skill_models = []
        for sk in extracted_skills:
            sk_m = JobSkill(
                id=uuid.uuid4(),
                job_id=job_record.id,
                skill_id=sk["skill_id"],
                raw_skill_text=sk["raw_skill_text"],
                canonical_skill_name=sk["canonical_skill_name"],
                requirement_type=sk["requirement_type"],
                source_section=sk["source_section"],
                evidence_text=sk["evidence_text"],
                confidence=sk["confidence"],
            )
            db.add(sk_m)
            skill_models.append(sk_m)

        # 10. Persist Experience Requirements
        exp_models = []
        for exp in parsed_data["experience_requirements"]:
            exp_m = JobExperienceRequirement(
                id=uuid.uuid4(),
                job_id=job_record.id,
                minimum_years=exp["minimum_years"],
                maximum_years=exp["maximum_years"],
                experience_text=exp["experience_text"],
                classification=exp["classification"],
            )
            db.add(exp_m)
            exp_models.append(exp_m)

        # 11. Persist Education Requirements
        edu_models = []
        for edu in parsed_data["education_requirements"]:
            edu_m = JobEducationRequirement(
                id=uuid.uuid4(),
                job_id=job_record.id,
                degree_level=edu["degree_level"],
                field=edu["field"],
                original_text=edu["original_text"],
                requirement_type=edu["requirement_type"],
            )
            db.add(edu_m)
            edu_models.append(edu_m)

        # 12. Persist Certifications
        cert_models = []
        for cert in parsed_data["certifications"]:
            cert_m = JobCertification(
                id=uuid.uuid4(),
                job_id=job_record.id,
                name=cert["name"],
                requirement_type=cert["requirement_type"],
            )
            db.add(cert_m)
            cert_models.append(cert_m)

        db.commit()
        db.refresh(job_record)

        return self._format_job_response(job_record)

    def create_job_from_pasted_text(
        self, data: JobCreatePastedSchema, user_id: uuid.UUID, db: Session
    ) -> StructuredJobResponse:
        """Creates and analyzes job from pasted text."""
        return self.process_and_persist_job(
            title=data.title,
            raw_text=data.raw_text,
            ingestion_type="PASTED",
            user_id=user_id,
            db=db,
            company=data.company,
            location=data.location,
            source_url=data.source_url,
        )

    def create_job_from_file_upload(
        self,
        file: UploadFile,
        title: str,
        user_id: uuid.UUID,
        db: Session,
        company: Optional[str] = None,
        location: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> StructuredJobResponse:
        """Validates uploaded PDF/DOCX job description, extracts text, and processes profile."""
        safe_name, ext = validate_file_metadata(file)

        file_bytes = file.file.read()
        file_size = len(file_bytes)
        validate_file_bytes(file_bytes[:16], file_size, ext)

        stored_filename, destination_path = generate_secure_storage_path(ext)
        try:
            with open(destination_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            logger.error(f"Failed to store job document: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal error saving file.")

        try:
            if ext == ".pdf":
                raw_text, _, _, _, _ = parse_pdf_document(destination_path)
            else:
                raw_text, _, _, _, _ = parse_docx_document(destination_path)
        finally:
            if os.path.exists(destination_path):
                os.remove(destination_path)

        return self.process_and_persist_job(
            title=title or safe_name,
            raw_text=raw_text,
            ingestion_type=ext.replace(".", "").upper(),
            user_id=user_id,
            db=db,
            company=company,
            location=location,
            source_url=source_url,
        )

    def get_user_jobs(self, user_id: uuid.UUID, db: Session) -> List[JobSummaryResponse]:
        """Lists summary of all jobs ingested by the user."""
        jobs = db.query(Job).filter(Job.user_id == user_id).order_by(Job.created_at.desc()).all()
        summaries = []
        for j in jobs:
            skills = j.skills
            required_cnt = sum(1 for s in skills if s.requirement_type == "REQUIRED")
            preferred_cnt = sum(1 for s in skills if s.requirement_type == "PREFERRED")

            min_exp = None
            if j.experience_requirements:
                valid_years = [e.minimum_years for e in j.experience_requirements if e.minimum_years is not None]
                if valid_years:
                    min_exp = min(valid_years)

            summaries.append(
                JobSummaryResponse(
                    id=j.id,
                    title=j.title,
                    normalized_role=j.normalized_role,
                    company=j.company,
                    location=j.location,
                    ingestion_type=j.ingestion_type,
                    total_skills=len(skills),
                    required_skills_count=required_cnt,
                    preferred_skills_count=preferred_cnt,
                    min_years_experience=min_exp,
                    created_at=j.created_at,
                )
            )
        return summaries

    def get_job_by_id(self, job_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> StructuredJobResponse:
        """Retrieves complete structured job profile."""
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job description with ID '{job_id}' not found.",
            )
        return self._format_job_response(job)

    def delete_job_by_id(self, job_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> None:
        """Deletes a job description and cascading entities."""
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job description with ID '{job_id}' not found.",
            )
        db.delete(job)
        db.commit()

    def _format_job_response(self, job: Job) -> StructuredJobResponse:
        """Formats SQLAlchemy Job model to StructuredJobResponse schema."""
        all_skills_list = []
        required_skills_list = []
        preferred_skills_list = []

        for s in job.skills:
            skill_model = s.skill
            taxonomy_src = [skill_model.taxonomy_source] if skill_model else []

            skill_schema = JobSkillSchema(
                id=s.id,
                skill_id=s.skill_id,
                raw_skill_text=s.raw_skill_text,
                canonical_skill_name=s.canonical_skill_name,
                requirement_type=s.requirement_type,
                source_section=s.source_section,
                evidence_text=s.evidence_text,
                confidence=s.confidence,
                taxonomy_sources=taxonomy_src,
            )
            all_skills_list.append(skill_schema)
            if s.requirement_type == "REQUIRED":
                required_skills_list.append(skill_schema)
            elif s.requirement_type == "PREFERRED":
                preferred_skills_list.append(skill_schema)

        return StructuredJobResponse(
            id=job.id,
            user_id=job.user_id,
            title=job.title,
            normalized_role=job.normalized_role,
            role_confidence=job.role_confidence,
            role_classification_method=job.role_classification_method,
            company=job.company,
            location=job.location,
            source_url=job.source_url,
            ingestion_type=job.ingestion_type,
            raw_text=job.raw_text,
            summary=job.summary,
            sections=[
                JobSectionSchema(
                    id=sec.id,
                    section_type=sec.section_type,
                    section_title=sec.section_title,
                    content_text=sec.content_text,
                    order_index=sec.order_index,
                )
                for sec in job.sections
            ],
            requirements=[
                JobRequirementSchema(
                    id=req.id,
                    original_text=req.original_text,
                    normalized_text=req.normalized_text,
                    requirement_category=req.requirement_category,
                    priority=req.priority,
                    source_section=req.source_section,
                    evidence_text=req.evidence_text,
                    confidence=req.confidence,
                )
                for req in job.requirements
            ],
            required_skills=required_skills_list,
            preferred_skills=preferred_skills_list,
            all_skills=all_skills_list,
            experience_requirements=[
                JobExperienceRequirementSchema(
                    id=exp.id,
                    minimum_years=exp.minimum_years,
                    maximum_years=exp.maximum_years,
                    experience_text=exp.experience_text,
                    classification=exp.classification,
                )
                for exp in job.experience_requirements
            ],
            education_requirements=[
                JobEducationRequirementSchema(
                    id=edu.id,
                    degree_level=edu.degree_level,
                    field=edu.field,
                    original_text=edu.original_text,
                    requirement_type=edu.requirement_type,
                )
                for edu in job.education_requirements
            ],
            certifications=[
                JobCertificationSchema(
                    id=cert.id,
                    name=cert.name,
                    requirement_type=cert.requirement_type,
                )
                for cert in job.certifications
            ],
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
