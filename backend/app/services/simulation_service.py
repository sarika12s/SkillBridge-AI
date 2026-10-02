"""What-If Gap-Closure Simulation Service for SkillBridge AI Phase 8.1.

Computes stateless, explainable counterfactual match scenarios by projecting the acquisition
of currently identified skill gaps without modifying any persisted database records.
Reuses the authoritative Phase 5 ScoringEngine as the single source of truth.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Set
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.matching import MatchAnalysis, SkillMatch, SkillGap, ScoreBreakdown
from app.models.resume import Resume
from app.models.job import Job
from app.models.skill import Skill
from app.models.learning import LearningResource
from app.models.career import CareerCompatibility, Occupation
from app.ai.matching.evaluators import AlignmentEvaluator
from app.ai.matching.scoring_engine import ScoringEngine
from app.ai.matching.gap_analyzer import SkillGapAnalyzer
from app.ai.career.career_engine import CareerEngine
from app.schemas.matching import (
    SimulationRequest,
    SimulationResponse,
    SimulatedSkillDetail,
    ProjectedGapState,
    CareerRoleProjection,
    ScoreBreakdownSchema,
)

logger = logging.getLogger(__name__)

GAP_STATUSES: Set[str] = {
    "MISSING_REQUIRED",
    "MISSING_PREFERRED",
    "PARTIAL_REQUIRED",
    "PARTIAL_PREFERRED",
    "RELATED_SUPPORT",
}


class SimulationService:
    """
    Stateless counterfactual simulator for skill gap closure.
    Calculates projected scores, deltas, coverage improvements, and learning-hour ROI
    without persisting any simulation data or mutating existing analyses.
    """

    def simulate_gap_closure(
        self,
        db: Session,
        user_id: UUID,
        match_analysis_id: UUID,
        simulated_skill_ids: List[UUID],
    ) -> SimulationResponse:
        """
        Executes a deterministic 'what-if' simulation for the specified skill gaps.
        """
        # 1. Fetch and validate MatchAnalysis entity
        analysis = (
            db.query(MatchAnalysis)
            .filter(MatchAnalysis.id == match_analysis_id)
            .first()
        )
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match analysis with ID '{match_analysis_id}' not found.",
            )

        # 2. Strict Tenant/User Authorization
        if analysis.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to simulate this match analysis.",
            )

        # 3. Validate simulated_skill_ids: Check duplicates
        if len(simulated_skill_ids) != len(set(simulated_skill_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate skill IDs provided in simulation request.",
            )

        # 4. Validate existence of simulated skills in the taxonomy
        skill_by_id: Dict[UUID, Skill] = {}
        if simulated_skill_ids:
            skills = db.query(Skill).filter(Skill.id.in_(simulated_skill_ids)).all()
            skill_by_id = {s.id: s for s in skills}
            if len(skills) != len(simulated_skill_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more simulated skill IDs do not exist in the taxonomy.",
                )

        # 5. Extract current eligible gap skills for this match analysis
        eligible_gap_skills: Dict[UUID, SkillMatch] = {}
        for m in analysis.skill_matches:
            if m.match_status in GAP_STATUSES:
                if m.canonical_skill_id:
                    eligible_gap_skills[m.canonical_skill_id] = m
                else:
                    # Resolve skill ID by canonical name if canonical_skill_id is null on match
                    canon = (
                        db.query(Skill)
                        .filter(func.lower(Skill.name) == func.lower(m.canonical_skill_name))
                        .first()
                    )
                    if canon:
                        eligible_gap_skills[canon.id] = m

        # Check gap relevance: Every simulated skill MUST be an identified gap
        for s_id in simulated_skill_ids:
            if s_id not in eligible_gap_skills:
                skill_name = skill_by_id[s_id].name if s_id in skill_by_id else str(s_id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Skill '{skill_name}' is not an identified gap for this job match.",
                )

        # 6. Construct Counterfactual In-Memory Matches
        simulated_set = set(simulated_skill_ids)
        simulated_names = {skill_by_id[s_id].name.lower() for s_id in simulated_set if s_id in skill_by_id}

        projected_matches: List[Dict[str, Any]] = []
        for m in analysis.skill_matches:
            is_simulated = (
                m.canonical_skill_id in simulated_set
                or m.canonical_skill_name.lower() in simulated_names
            )

            if is_simulated and m.match_status in GAP_STATUSES:
                # Counterfactually convert gap to direct match
                target_status = "MATCHED_REQUIRED" if m.priority == "REQUIRED" else "MATCHED_PREFERRED"
                projected_matches.append({
                    "job_skill_id": m.job_skill_id,
                    "resume_skill_id": m.resume_skill_id,
                    "canonical_skill_id": m.canonical_skill_id,
                    "canonical_skill_name": m.canonical_skill_name,
                    "match_type": "DIRECT_MATCH",
                    "match_status": target_status,
                    "priority": m.priority,
                    "confidence": 1.0,
                    "similarity_score": 1.0,
                    "resume_evidence": f"[Simulated Acquisition] Candidate hypothetically demonstrates proficiency in {m.canonical_skill_name}.",
                    "job_evidence": m.job_evidence,
                    "explanation": f"Simulated acquisition: Candidate hypothetically fulfills '{m.canonical_skill_name}' requirement.",
                })
            else:
                # Maintain original match
                projected_matches.append({
                    "job_skill_id": m.job_skill_id,
                    "resume_skill_id": m.resume_skill_id,
                    "canonical_skill_id": m.canonical_skill_id,
                    "canonical_skill_name": m.canonical_skill_name,
                    "match_type": m.match_type,
                    "match_status": m.match_status,
                    "priority": m.priority,
                    "confidence": m.confidence,
                    "similarity_score": m.similarity_score,
                    "resume_evidence": m.resume_evidence,
                    "job_evidence": m.job_evidence,
                    "explanation": m.explanation,
                })

        # 7. Reconstruct Alignment Dict
        job = db.query(Job).filter(Job.id == analysis.job_id).first()
        resume = db.query(Resume).filter(Resume.id == analysis.resume_id).first()

        exp_align = AlignmentEvaluator.evaluate_experience(
            resume, job.experience_requirements if job else []
        )
        edu_align = AlignmentEvaluator.evaluate_education(
            resume, job.education_requirements if job else []
        )
        cert_align = AlignmentEvaluator.evaluate_certifications(
            resume, job.certifications if job else []
        )
        alignment_dict = {**exp_align, **edu_align, **cert_align}

        # 8. Re-evaluate Scores via Authoritative Phase 5 ScoringEngine
        scoring_result = ScoringEngine.calculate_scores(projected_matches, alignment_dict)
        projected_compatibility = scoring_result["compatibility_score"]
        projected_ats = scoring_result["ats_readiness_score"]
        projected_breakdowns = [
            ScoreBreakdownSchema.model_validate(b) for b in scoring_result["score_breakdowns"]
        ]

        compatibility_delta = round(projected_compatibility - analysis.compatibility_score, 2)
        ats_delta = round(projected_ats - analysis.ats_readiness_score, 2)

        # 9. Calculate Required and Preferred Coverage Deltas
        current_req_cov = next(
            (b.score for b in analysis.score_breakdowns if b.component_name == "required_skill_coverage"),
            100.0,
        )
        current_pref_cov = next(
            (b.score for b in analysis.score_breakdowns if b.component_name == "preferred_skill_coverage"),
            100.0,
        )

        projected_req_cov = next(
            (b.score for b in projected_breakdowns if b.component_name == "required_skill_coverage"),
            100.0,
        )
        projected_pref_cov = next(
            (b.score for b in projected_breakdowns if b.component_name == "preferred_skill_coverage"),
            100.0,
        )

        req_cov_delta = round(projected_req_cov - current_req_cov, 2)
        pref_cov_delta = round(projected_pref_cov - current_pref_cov, 2)

        # 10. Evaluate Projected Gap State via SkillGapAnalyzer
        projected_gaps = SkillGapAnalyzer.identify_gaps(projected_matches)
        remaining_required = [
            g["canonical_skill_name"] for g in projected_gaps if g["priority"] == "REQUIRED"
        ]
        remaining_preferred = [
            g["canonical_skill_name"] for g in projected_gaps if g["priority"] != "REQUIRED"
        ]
        closed_gaps = [
            skill_by_id[s_id].name for s_id in simulated_skill_ids if s_id in skill_by_id
        ]

        # 11. Calculate Learning Effort & Projected ROI
        simulated_details: List[SimulatedSkillDetail] = []
        total_hours_list: List[float] = []

        for s_id in simulated_skill_ids:
            skill_obj = skill_by_id[s_id]
            gap_m = eligible_gap_skills.get(s_id)
            cur_status = gap_m.match_status if gap_m else "MISSING_REQUIRED"
            priority = gap_m.priority if gap_m else "REQUIRED"
            gap_reason = (
                gap_m.explanation
                if gap_m
                else f"Skill '{skill_obj.name}' was missing from candidate profile for this role."
            )

            # Query real learning resources for this skill
            skill_resources = (
                db.query(LearningResource)
                .filter(LearningResource.skill_id == s_id)
                .all()
            )
            res_count = len(skill_resources)
            if res_count > 0:
                avg_hours = round(sum(r.estimated_hours for r in skill_resources) / res_count, 1)
                total_hours_list.append(avg_hours)
            else:
                avg_hours = None

            simulated_details.append(
                SimulatedSkillDetail(
                    skill_id=s_id,
                    canonical_skill_name=skill_obj.name,
                    priority=priority,
                    current_status=cur_status,
                    gap_reason=gap_reason,
                    estimated_learning_hours=avg_hours,
                    learning_resources_count=res_count,
                )
            )

        total_estimated_hours = round(sum(total_hours_list), 1) if total_hours_list else None
        if total_estimated_hours and total_estimated_hours > 0 and compatibility_delta > 0:
            learning_hour_roi = round(compatibility_delta / total_estimated_hours, 2)
        elif total_estimated_hours and total_estimated_hours > 0 and compatibility_delta == 0:
            learning_hour_roi = 0.0
        else:
            learning_hour_roi = None

        # 12. Optional Target Career Role Projection
        target_role_projection: Optional[CareerRoleProjection] = None
        existing_compat = (
            db.query(CareerCompatibility)
            .filter(
                CareerCompatibility.resume_id == analysis.resume_id,
                CareerCompatibility.user_id == user_id,
            )
            .order_by(CareerCompatibility.compatibility_score.desc())
            .first()
        )
        if existing_compat and resume:
            occ = (
                db.query(Occupation)
                .filter(Occupation.id == existing_compat.occupation_id)
                .first()
            )
            if occ:
                career_engine = CareerEngine(db)
                candidate_skills = career_engine._extract_candidate_skill_map(resume)
                projected_cand_skills = dict(candidate_skills)
                for s_id in simulated_skill_ids:
                    s_obj = skill_by_id[s_id]
                    norm = s_obj.name.lower().strip()
                    projected_cand_skills[norm] = {
                        "canonical_name": s_obj.name,
                        "category": s_obj.category or "TECHNICAL_SKILL",
                        "mentions": 1,
                        "has_experience": True,
                    }
                proj_occ_res = career_engine._score_single_occupation(
                    resume, occ, projected_cand_skills
                )
                target_role_projection = CareerRoleProjection(
                    occupation_id=occ.id,
                    occupation_title=occ.title,
                    current_compatibility_score=existing_compat.compatibility_score,
                    projected_compatibility_score=proj_occ_res["compatibility_score"],
                    compatibility_score_delta=round(
                        proj_occ_res["compatibility_score"] - existing_compat.compatibility_score,
                        2,
                    ),
                )

        # 13. Construct Explainability Narrative
        explanation_parts = []
        skill_names_str = (
            ", ".join(f"'{d.canonical_skill_name}'" for d in simulated_details)
            if simulated_details
            else "none"
        )
        explanation_parts.append(
            f"Simulating acquisition of {len(simulated_skill_ids)} skill(s) ({skill_names_str}) closes {len(closed_gaps)} gap(s)."
        )
        explanation_parts.append(
            f"Job Compatibility changes by {compatibility_delta:+.1f}% (from {analysis.compatibility_score:.1f}% to {projected_compatibility:.1f}%), "
            f"and SkillBridge ATS Readiness changes by {ats_delta:+.1f}% (from {analysis.ats_readiness_score:.1f}% to {projected_ats:.1f}%)."
        )
        if req_cov_delta != 0:
            explanation_parts.append(
                f"Required skill coverage changes by {req_cov_delta:+.1f}% (from {current_req_cov:.1f}% to {projected_req_cov:.1f}%)."
            )
        if pref_cov_delta != 0:
            explanation_parts.append(
                f"Preferred skill coverage changes by {pref_cov_delta:+.1f}% (from {current_pref_cov:.1f}% to {projected_pref_cov:.1f}%)."
            )
        if learning_hour_roi is not None and total_estimated_hours is not None:
            explanation_parts.append(
                f"Estimated learning effort is {total_estimated_hours:.1f} hours across available curriculum resources, yielding an estimated ROI of +{learning_hour_roi:.2f} compatibility points per study hour."
            )
        explanation = " ".join(explanation_parts)

        # Note: Zero database writes performed (no add, no flush, no commit)
        return SimulationResponse(
            match_analysis_id=analysis.id,
            job_id=analysis.job_id,
            job_title=job.title if job else "Target Job",
            resume_id=analysis.resume_id,
            current_ats_score=analysis.ats_readiness_score,
            projected_ats_score=projected_ats,
            ats_score_delta=ats_delta,
            current_compatibility_score=analysis.compatibility_score,
            projected_compatibility_score=projected_compatibility,
            compatibility_score_delta=compatibility_delta,
            current_required_coverage=current_req_cov,
            projected_required_coverage=projected_req_cov,
            required_coverage_delta=req_cov_delta,
            current_preferred_coverage=current_pref_cov,
            projected_preferred_coverage=projected_pref_cov,
            preferred_coverage_delta=pref_cov_delta,
            simulated_skills=simulated_details,
            gap_state=ProjectedGapState(
                closed_gaps=closed_gaps,
                remaining_required_gaps=remaining_required,
                remaining_preferred_gaps=remaining_preferred,
                total_initial_gaps=len(analysis.skill_gaps),
                total_remaining_gaps=len(remaining_required) + len(remaining_preferred),
            ),
            projected_score_breakdowns=projected_breakdowns,
            total_estimated_learning_hours=total_estimated_hours,
            learning_hour_roi=learning_hour_roi,
            explanation=explanation,
            target_role_projection=target_role_projection,
        )


simulation_service = SimulationService()
