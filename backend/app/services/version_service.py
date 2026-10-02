"""Resume Version Management and Comparison Service."""

import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.resume import Resume, ResumeSection
from app.models.skill import ResumeSkill
from app.models.matching import MatchAnalysis
from app.schemas.dashboard import (
    ResumeVersionSummary,
    ResumeVersionComparisonResponse,
)


class VersionService:
    def __init__(self, db: Session):
        self.db = db

    def list_resume_versions(self, user_id: uuid.UUID) -> List[ResumeVersionSummary]:
        """Lists all resume versions for the authenticated user ordered by version number."""
        resumes = (
            self.db.query(Resume)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.version.asc(), Resume.created_at.asc())
            .all()
        )

        summaries = []
        for r in resumes:
            last_match = (
                self.db.query(MatchAnalysis)
                .filter(MatchAnalysis.resume_id == r.id)
                .order_by(MatchAnalysis.created_at.desc())
                .first()
            )
            summaries.append(
                ResumeVersionSummary(
                    id=r.id,
                    version=r.version,
                    title=r.title,
                    file_name=r.file_name,
                    file_type=r.file_type,
                    file_size_bytes=r.file_size_bytes,
                    parsing_status=r.parsing_status,
                    skills_count=len(r.skills) if r.skills else 0,
                    created_at=r.created_at,
                    last_analysis_at=last_match.created_at if last_match else None,
                )
            )
        return summaries

    def compare_resume_versions(
        self,
        user_id: uuid.UUID,
        resume_id_1: uuid.UUID,
        resume_id_2: uuid.UUID,
    ) -> ResumeVersionComparisonResponse:
        """
        Compares two distinct resume versions belonging to the authenticated user.
        Evaluates added/retained/removed skills, section modifications, and score comparability.
        """
        r1 = (
            self.db.query(Resume)
            .options(joinedload(Resume.skills), joinedload(Resume.sections))
            .filter(Resume.id == resume_id_1, Resume.user_id == user_id)
            .first()
        )
        r2 = (
            self.db.query(Resume)
            .options(joinedload(Resume.skills), joinedload(Resume.sections))
            .filter(Resume.id == resume_id_2, Resume.user_id == user_id)
            .first()
        )

        if not r1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume version '{resume_id_1}' not found or access denied.",
            )
        if not r2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume version '{resume_id_2}' not found or access denied.",
            )

        # 1. Compare Skills
        skills_v1 = {
            (rs.canonical_skill_name or rs.raw_skill_text).strip(): rs
            for rs in (r1.skills or [])
        }
        skills_v2 = {
            (rs.canonical_skill_name or rs.raw_skill_text).strip(): rs
            for rs in (r2.skills or [])
        }

        names_v1 = set(skills_v1.keys())
        names_v2 = set(skills_v2.keys())

        new_skills = sorted(list(names_v2 - names_v1))
        retained_skills = sorted(list(names_v1 & names_v2))
        removed_skills = sorted(list(names_v1 - names_v2))

        # 2. Compare Skill Evidence
        evidence_changes = []
        for sk in retained_skills:
            ev1 = skills_v1[sk].evidence_sentence or ""
            ev2 = skills_v2[sk].evidence_sentence or ""
            sec1 = skills_v1[sk].source_section or "SKILLS"
            sec2 = skills_v2[sk].source_section or "SKILLS"

            if ev1 != ev2 or sec1 != sec2:
                evidence_changes.append({
                    "skill_name": sk,
                    "previous_section": sec1,
                    "new_section": sec2,
                    "previous_evidence": ev1,
                    "new_evidence": ev2,
                    "strengthened": sec2 in ["EXPERIENCE", "PROJECTS"] and sec1 not in ["EXPERIENCE", "PROJECTS"],
                })

        # 3. Section Changes
        sections_v1 = {s.section_type: s for s in (r1.sections or [])}
        sections_v2 = {s.section_type: s for s in (r2.sections or [])}
        section_changes = {
            "v1_section_count": len(sections_v1),
            "v2_section_count": len(sections_v2),
            "new_sections": list(set(sections_v2.keys()) - set(sections_v1.keys())),
            "removed_sections": list(set(sections_v1.keys()) - set(sections_v2.keys())),
            "character_delta": r2.character_count - r1.character_count,
        }

        # 4. Score Comparability Guard
        # Check latest match analysis for each resume
        match_v1 = (
            self.db.query(MatchAnalysis)
            .filter(MatchAnalysis.resume_id == r1.id)
            .order_by(MatchAnalysis.created_at.desc())
            .first()
        )
        match_v2 = (
            self.db.query(MatchAnalysis)
            .filter(MatchAnalysis.resume_id == r2.id)
            .order_by(MatchAnalysis.created_at.desc())
            .first()
        )

        ats_v1 = match_v1.ats_readiness_score if match_v1 else None
        ats_v2 = match_v2.ats_readiness_score if match_v2 else None
        ats_delta = (ats_v2 - ats_v1) if (ats_v1 is not None and ats_v2 is not None) else None

        job_comp_v1 = match_v1.compatibility_score if match_v1 else None
        job_comp_v2 = match_v2.compatibility_score if match_v2 else None
        job_delta = None
        is_same_job = False
        target_job_title = None
        comparability_notes = ""

        if match_v1 and match_v2:
            if match_v1.job_id == match_v2.job_id:
                is_same_job = True
                job_delta = round(job_comp_v2 - job_comp_v1, 1)
                target_job_title = match_v2.job.title if match_v2.job else "Target Role"
                comparability_notes = f"Directly comparable analysis against consistent job role: '{target_job_title}'."
                if match_v1.scoring_version != match_v2.scoring_version:
                    comparability_notes += " Note: Scoring methodology version updated between analyses."
            else:
                is_same_job = False
                job_delta = None
                job1_title = match_v1.job.title if match_v1.job else "Job A"
                job2_title = match_v2.job.title if match_v2.job else "Job B"
                comparability_notes = (
                    f"Scores are not directly comparable because the target job changed "
                    f"('{job1_title}' vs '{job2_title}')."
                )
        else:
            comparability_notes = "One or both resume versions have not been analyzed against a job description."

        return ResumeVersionComparisonResponse(
            resume_v1_id=r1.id,
            resume_v1_version=r1.version,
            resume_v1_title=r1.title,
            resume_v1_created_at=r1.created_at,
            resume_v2_id=r2.id,
            resume_v2_version=r2.version,
            resume_v2_title=r2.title,
            resume_v2_created_at=r2.created_at,
            new_skills=new_skills,
            retained_skills=retained_skills,
            removed_skills=removed_skills,
            skill_evidence_changes=evidence_changes,
            section_changes=section_changes,
            ats_score_v1=ats_v1,
            ats_score_v2=ats_v2,
            ats_score_delta=round(ats_delta, 1) if ats_delta is not None else None,
            job_compatibility_v1=job_comp_v1,
            job_compatibility_v2=job_comp_v2,
            job_compatibility_delta=job_delta,
            is_same_job_comparison=is_same_job,
            target_job_title=target_job_title,
            comparability_notes=comparability_notes,
        )
