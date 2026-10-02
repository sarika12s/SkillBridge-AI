"""Matching Service orchestrating Resume-to-Job analysis, skill gap extraction, and score persistence."""

import logging
import uuid
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.ai.matching.config import matching_config
from app.ai.matching.matcher import SkillMatchingEngine
from app.ai.matching.evaluators import AlignmentEvaluator
from app.ai.matching.gap_analyzer import SkillGapAnalyzer
from app.ai.matching.scoring_engine import ScoringEngine
from app.ai.matching.explainability import ExplainabilityEngine
from app.models.resume import Resume
from app.models.job import Job
from app.models.skill import Skill, SkillRelationship
from app.models.matching import (
    MatchAnalysis,
    SkillMatch,
    SkillGap,
    ScoreBreakdown,
)
from app.schemas.matching import (
    MatchAnalysisResponse,
    SkillMatchSchema,
    SkillGapSchema,
    ScoreBreakdownSchema,
    StructuredAlignmentSchema,
    ExplainabilitySummarySchema,
    ResumeSkillGapsResponse,
)

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Coordinates end-to-end resume-vs-job analysis, executing matching engines,
    calculating explainable scores, and persisting verifiable audit records.
    """

    def __init__(self):
        self.matcher = SkillMatchingEngine()

    def analyze_match(
        self,
        db: Session,
        user_id: UUID,
        resume_id: UUID,
        job_id: UUID,
    ) -> MatchAnalysisResponse:
        """
        Executes complete hybrid match analysis between an existing resume and job description.
        """
        # 1. Fetch and validate Resume
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID '{resume_id}' not found.",
            )

        # 2. Fetch and validate Job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job description with ID '{job_id}' not found.",
            )

        # 3. Load Canonical Skills and Relationships
        canonical_skills = db.query(Skill).all()
        canonical_map = {s.id: s for s in canonical_skills}
        relationships = db.query(SkillRelationship).all()

        resume_skills = resume.skills or []
        job_skills = job.skills or []

        # 4. Execute Skill Matching Engine for each Job Skill
        matches: List[Dict[str, Any]] = []
        for j_skill in job_skills:
            m = self.matcher.match_job_skill_to_resume_skills(
                job_skill=j_skill,
                resume_skills=resume_skills,
                canonical_skills_map=canonical_map,
                relationships=relationships,
            )
            matches.append(m)

        # 5. Evaluate Structured Alignments (Experience, Education, Certifications)
        exp_align = AlignmentEvaluator.evaluate_experience(resume, job.experience_requirements or [])
        edu_align = AlignmentEvaluator.evaluate_education(resume, job.education_requirements or [])
        cert_align = AlignmentEvaluator.evaluate_certifications(resume, job.certifications or [])

        alignment_dict = {
            **exp_align,
            **edu_align,
            **cert_align,
        }

        # 6. Extract and Prioritize Skill Gaps
        gaps = SkillGapAnalyzer.identify_gaps(matches)

        # 7. Compute Scores and Component Breakdowns
        scoring_result = ScoringEngine.calculate_scores(matches, alignment_dict)
        compatibility_score = scoring_result["compatibility_score"]
        ats_readiness_score = scoring_result["ats_readiness_score"]
        score_breakdowns_data = scoring_result["score_breakdowns"]

        # 8. Generate Factual Explainability Reports
        explainability = ExplainabilityEngine.generate_explanation(
            matches=matches,
            gaps=gaps,
            alignment=alignment_dict,
            scores=scoring_result,
            job_title=job.title,
        )

        # 9. Persist MatchAnalysis Entity
        analysis = MatchAnalysis(
            id=uuid.uuid4(),
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            compatibility_score=compatibility_score,
            ats_readiness_score=ats_readiness_score,
            matching_engine_version=matching_config.MATCHING_ENGINE_VERSION,
            scoring_version=matching_config.SCORING_VERSION,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            taxonomy_versions=matching_config.TAXONOMY_VERSIONS,
            summary_explanation=explainability["summary_explanation"],
        )
        db.add(analysis)
        db.flush()

        # 10. Persist Skill Matches
        skill_match_records = []
        for m in matches:
            sm = SkillMatch(
                id=uuid.uuid4(),
                match_analysis_id=analysis.id,
                job_skill_id=m.get("job_skill_id"),
                resume_skill_id=m.get("resume_skill_id"),
                canonical_skill_id=m.get("canonical_skill_id"),
                canonical_skill_name=m["canonical_skill_name"],
                match_type=m["match_type"],
                match_status=m["match_status"],
                priority=m["priority"],
                confidence=m["confidence"],
                similarity_score=m.get("similarity_score"),
                resume_evidence=m.get("resume_evidence"),
                job_evidence=m.get("job_evidence"),
                explanation=m["explanation"],
            )
            db.add(sm)
            skill_match_records.append(sm)

        # 11. Persist Skill Gaps
        skill_gap_records = []
        for g in gaps:
            sg = SkillGap(
                id=uuid.uuid4(),
                match_analysis_id=analysis.id,
                canonical_skill_name=g["canonical_skill_name"],
                priority=g["priority"],
                status=g["status"],
                importance_weight=g["importance_weight"],
                explanation=g["explanation"],
                job_evidence=g.get("job_evidence"),
            )
            db.add(sg)
            skill_gap_records.append(sg)

        # 12. Persist Score Breakdowns
        breakdown_records = []
        for b in score_breakdowns_data:
            sb = ScoreBreakdown(
                id=uuid.uuid4(),
                match_analysis_id=analysis.id,
                component_name=b["component_name"],
                score=b["score"],
                max_possible=b["max_possible"],
                weight=b["weight"],
                weighted_score=b["weighted_score"],
                explanation=b["explanation"],
            )
            db.add(sb)
            breakdown_records.append(sb)

        db.commit()
        db.refresh(analysis)

        return self._format_response(
            analysis=analysis,
            job=job,
            matches=skill_match_records,
            gaps=skill_gap_records,
            breakdowns=breakdown_records,
            alignment=alignment_dict,
            explainability=explainability,
        )

    def get_analysis_by_id(
        self,
        db: Session,
        analysis_id: UUID,
        user_id: UUID,
    ) -> MatchAnalysisResponse:
        """Retrieves an existing match analysis."""
        analysis = (
            db.query(MatchAnalysis)
            .filter(MatchAnalysis.id == analysis_id, MatchAnalysis.user_id == user_id)
            .first()
        )
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match analysis with ID '{analysis_id}' not found.",
            )

        job = db.query(Job).filter(Job.id == analysis.job_id).first()
        resume = db.query(Resume).filter(Resume.id == analysis.resume_id).first()

        exp_align = AlignmentEvaluator.evaluate_experience(resume, job.experience_requirements or [])
        edu_align = AlignmentEvaluator.evaluate_education(resume, job.education_requirements or [])
        cert_align = AlignmentEvaluator.evaluate_certifications(resume, job.certifications or [])
        alignment_dict = {**exp_align, **edu_align, **cert_align}

        match_dicts = [
            {
                "canonical_skill_name": m.canonical_skill_name,
                "match_type": m.match_type,
                "priority": m.priority,
            }
            for m in analysis.skill_matches
        ]
        gap_dicts = [
            {
                "canonical_skill_name": g.canonical_skill_name,
                "priority": g.priority,
            }
            for g in analysis.skill_gaps
        ]
        explainability = ExplainabilityEngine.generate_explanation(
            matches=match_dicts,
            gaps=gap_dicts,
            alignment=alignment_dict,
            scores={"compatibility_score": analysis.compatibility_score, "ats_readiness_score": analysis.ats_readiness_score},
            job_title=job.title if job else "Target Role",
        )

        return self._format_response(
            analysis=analysis,
            job=job,
            matches=analysis.skill_matches,
            gaps=analysis.skill_gaps,
            breakdowns=analysis.score_breakdowns,
            alignment=alignment_dict,
            explainability=explainability,
        )

    def get_or_create_match(
        self,
        db: Session,
        user_id: UUID,
        resume_id: UUID,
        job_id: UUID,
    ) -> MatchAnalysisResponse:
        """Finds latest analysis between resume and job or executes fresh analysis."""
        latest = (
            db.query(MatchAnalysis)
            .filter(
                MatchAnalysis.resume_id == resume_id,
                MatchAnalysis.job_id == job_id,
                MatchAnalysis.user_id == user_id,
            )
            .order_by(MatchAnalysis.created_at.desc())
            .first()
        )
        if latest:
            return self.get_analysis_by_id(db, latest.id, user_id)
        return self.analyze_match(db, user_id, resume_id, job_id)

    def get_resume_skill_gaps(
        self,
        db: Session,
        resume_id: UUID,
        user_id: UUID,
    ) -> ResumeSkillGapsResponse:
        """Retrieves aggregated skill gaps for a resume across recent analyses."""
        latest_analysis = (
            db.query(MatchAnalysis)
            .filter(MatchAnalysis.resume_id == resume_id, MatchAnalysis.user_id == user_id)
            .order_by(MatchAnalysis.created_at.desc())
            .first()
        )
        if not latest_analysis:
            return ResumeSkillGapsResponse(
                resume_id=resume_id,
                total_gaps=0,
                required_gaps=[],
                preferred_gaps=[],
            )

        gaps = latest_analysis.skill_gaps
        req_gaps = [SkillGapSchema.model_validate(g) for g in gaps if g.priority == "REQUIRED"]
        pref_gaps = [SkillGapSchema.model_validate(g) for g in gaps if g.priority != "REQUIRED"]

        return ResumeSkillGapsResponse(
            resume_id=resume_id,
            total_gaps=len(gaps),
            required_gaps=req_gaps,
            preferred_gaps=pref_gaps,
        )

    def _format_response(
        self,
        analysis: MatchAnalysis,
        job: Optional[Job],
        matches: List[SkillMatch],
        gaps: List[SkillGap],
        breakdowns: List[ScoreBreakdown],
        alignment: Dict[str, Any],
        explainability: Dict[str, Any],
    ) -> MatchAnalysisResponse:
        """Helper to assemble a clean Pydantic response."""
        return MatchAnalysisResponse(
            id=analysis.id,
            user_id=analysis.user_id,
            resume_id=analysis.resume_id,
            job_id=analysis.job_id,
            job_title=job.title if job else "Unknown Job",
            job_company=job.company if job else None,
            compatibility_score=analysis.compatibility_score,
            ats_readiness_score=analysis.ats_readiness_score,
            matching_engine_version=analysis.matching_engine_version,
            scoring_version=analysis.scoring_version,
            embedding_model=analysis.embedding_model,
            taxonomy_versions=analysis.taxonomy_versions,
            summary_explanation=analysis.summary_explanation,
            created_at=analysis.created_at,
            skill_matches=[SkillMatchSchema.model_validate(m) for m in matches],
            skill_gaps=[SkillGapSchema.model_validate(g) for g in gaps],
            score_breakdowns=[ScoreBreakdownSchema.model_validate(b) for b in breakdowns],
            alignment=StructuredAlignmentSchema(
                experience_status=alignment.get("experience_status", "UNKNOWN"),
                experience_explanation=alignment.get("experience_explanation", ""),
                resume_years=alignment.get("resume_years"),
                required_years=alignment.get("required_years"),
                education_status=alignment.get("education_status", "UNKNOWN"),
                education_explanation=alignment.get("education_explanation", ""),
                resume_degree=alignment.get("resume_degree"),
                required_degree=alignment.get("required_degree"),
                certification_status=alignment.get("certification_status", "UNKNOWN"),
                certification_explanation=alignment.get("certification_explanation", ""),
                matched_certifications=alignment.get("matched_certifications", []),
                missing_certifications=alignment.get("missing_certifications", []),
            ),
            explainability=ExplainabilitySummarySchema(
                strengths=explainability.get("strengths", []),
                critical_gaps=explainability.get("critical_gaps", []),
                positive_factors=explainability.get("positive_factors", []),
                negative_factors=explainability.get("negative_factors", []),
                uncertainties=explainability.get("uncertainties", []),
            ),
        )


matching_service = MatchingService()
