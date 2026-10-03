"""Prioritization Service for SkillBridge AI Phase 8.4.

A stateless, compute-on-read service that evaluates skill dependencies,
calculates mathematical priority scores, and selects the Next Best Skill
for personalized learning paths targeting students and freshers.
Strictly non-mutating: zero database writes, zero historical changes.
"""

from collections import deque
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.ai.learning.dependency_graph import SkillDependencyGraph
from app.ai.learning.prioritizer import (
    calculate_dependency_leverage,
    calculate_gap_impact,
    calculate_learning_efficiency,
    calculate_priority_score,
    calculate_role_criticality,
    clamp_learning_hours,
    evaluate_readiness,
    find_downstream_unlocked_skills,
    generate_deterministic_explanation,
    select_next_best_skill,
    sort_prioritized_skills,
)
from app.ai.matching.evaluators import AlignmentEvaluator
from app.ai.matching.scoring_engine import ScoringEngine
from app.models.career import CareerCompatibility, Occupation, OccupationSkill
from app.models.job import Job, JobSkill
from app.models.learning import LearningPath, LearningPathItem
from app.models.matching import MatchAnalysis, SkillMatch
from app.models.resume import Resume
from app.models.skill import ResumeSkill, Skill, SkillRelationship
from app.schemas.prioritized_learning import (
    DiagnosticCycleSchema,
    NextBestSkillSchema,
    PrioritizedRoadmapResponse,
    PrioritizedSkillSchema,
)

logger = logging.getLogger(__name__)

FALLBACK_HOURS: float = 6.0


class PrioritizationService:
    """Computes explainable, deterministic roadmap prioritization and Next Best Skill selection."""

    def __init__(self, db: Session):
        self.db = db
        self.dep_graph = SkillDependencyGraph(db=db)

    def get_prioritized_roadmap(
        self,
        path_id: UUID,
        user_id: UUID,
        include_implicit: bool = True,
    ) -> PrioritizedRoadmapResponse:
        """
        Computes the prioritized skill roadmap for a user's learning path.
        Completely read-only: does not modify or commit any database state.
        """
        # 1. Fetch LearningPath with joined relationships
        path = (
            self.db.query(LearningPath)
            .options(
                joinedload(LearningPath.items).joinedload(LearningPathItem.skill),
                joinedload(LearningPath.items).joinedload(LearningPathItem.resource),
                joinedload(LearningPath.occupation).joinedload(Occupation.skills),
                joinedload(LearningPath.job).joinedload(Job.skills),
                joinedload(LearningPath.resume),
            )
            .filter(LearningPath.id == path_id)
            .first()
        )
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning path with ID '{path_id}' not found.",
            )

        # Enforce Tenant Isolation
        if path.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning path not found or access denied.",
            )

        # 2. Extract Candidate's Satisfied Skills (Active Resume + Completed Path Items)
        satisfied_skill_ids: Set[UUID] = set()
        satisfied_skill_names: Set[str] = set()

        # Resume-evidenced skills (confidence >= 0.85)
        resume_skills = (
            self.db.query(ResumeSkill)
            .filter(ResumeSkill.resume_id == path.resume_id)
            .all()
        )
        for rs in resume_skills:
            if rs.confidence >= 0.85:
                satisfied_skill_ids.add(rs.skill_id)
                satisfied_skill_names.add(rs.canonical_skill_name.lower().strip())

        # Path items marked COMPLETED
        for item in path.items:
            if item.status == "COMPLETED":
                satisfied_skill_ids.add(item.skill_id)
                if item.skill:
                    satisfied_skill_names.add(item.skill.name.lower().strip())

        # 3. Load Prerequisite Graph from Database
        prereq_rels = (
            self.db.query(SkillRelationship)
            .options(
                joinedload(SkillRelationship.source_skill),
                joinedload(SkillRelationship.target_skill),
            )
            .filter(SkillRelationship.relationship_type == "PREREQUISITE_OF")
            .all()
        )

        # Build adjacency maps:
        # source_skill_id is prerequisite of target_skill_id (source -> target)
        prereq_to_dependents_id: Dict[UUID, List[UUID]] = {}
        dependent_to_prereqs_id: Dict[UUID, List[UUID]] = {}
        all_skill_lookup: Dict[UUID, Skill] = {}

        for rel in prereq_rels:
            src_id = rel.source_skill_id
            tgt_id = rel.target_skill_id

            if rel.source_skill:
                all_skill_lookup[src_id] = rel.source_skill
            if rel.target_skill:
                all_skill_lookup[tgt_id] = rel.target_skill

            prereq_to_dependents_id.setdefault(src_id, []).append(tgt_id)
            dependent_to_prereqs_id.setdefault(tgt_id, []).append(src_id)

        # Also register all skills from path items into lookup
        for item in path.items:
            if item.skill:
                all_skill_lookup[item.skill.id] = item.skill

        # 4. Check for cycles in the dependency graph
        cycle_paths = self.dep_graph.detect_cycles()
        diagnostic_cycles = DiagnosticCycleSchema(
            has_cycle=len(cycle_paths) > 0,
            cycle_paths=cycle_paths,
        )

        # 5. Determine Target-Relevant Skills and Requirements
        target_skills_dict: Dict[UUID, Dict[str, Any]] = {}
        match_analysis: Optional[MatchAnalysis] = None
        alignment_dict: Dict[str, Any] = {}

        if path.target_type == "JOB" and path.target_job_id:
            job = path.job
            if job:
                for js in job.skills:
                    all_skill_lookup[js.skill_id] = js.skill
                    target_skills_dict[js.skill_id] = {
                        "requirement_type": js.requirement_type,
                        "importance_weight": 1.0,
                        "skill": js.skill,
                        "skill_name": js.canonical_skill_name,
                    }

            # Fetch MatchAnalysis for baseline scoring and gap statuses
            match_analysis = (
                self.db.query(MatchAnalysis)
                .options(joinedload(MatchAnalysis.skill_matches))
                .filter(
                    MatchAnalysis.resume_id == path.resume_id,
                    MatchAnalysis.job_id == path.target_job_id,
                    MatchAnalysis.user_id == user_id,
                )
                .first()
            )

            if match_analysis and job:
                # Pre-build alignment dict for delta simulation
                resume = path.resume
                exp_align = AlignmentEvaluator.evaluate_experience(
                    resume, job.experience_requirements or []
                )
                edu_align = AlignmentEvaluator.evaluate_education(
                    resume, job.education_requirements or []
                )
                cert_align = AlignmentEvaluator.evaluate_certifications(
                    resume, job.certifications or []
                )
                alignment_dict = {**exp_align, **edu_align, **cert_align}

        elif path.target_type == "CAREER" and path.target_occupation_id:
            occ = path.occupation
            if occ:
                for os in occ.skills:
                    all_skill_lookup[os.skill_id] = os.skill
                    target_skills_dict[os.skill_id] = {
                        "requirement_type": os.requirement_type,
                        "importance_weight": os.importance_weight,
                        "skill": os.skill,
                        "skill_name": os.skill.name if os.skill else "Skill",
                    }

        # Fallback: if target has no explicit skills in DB, populate from path items
        if not target_skills_dict:
            for item in path.items:
                if item.skill_id:
                    target_skills_dict[item.skill_id] = {
                        "requirement_type": "REQUIRED",
                        "importance_weight": 1.0,
                        "skill": item.skill,
                        "skill_name": item.skill.name if item.skill else "Skill",
                    }

        target_skill_ids = set(target_skills_dict.keys())

        # 6. Evaluate Implicit Prerequisites (if include_implicit is True)
        # Traverse upstream (dependent -> prereqs) for each target skill.
        # If an unacquired prerequisite is not in target_skill_ids, surface it as an implicit prerequisite.
        implicit_prerequisites: Dict[UUID, Set[UUID]] = {}  # prereq_id -> set of target_skill_ids that need it

        if include_implicit:
            for t_id in target_skill_ids:
                visited_upstream: Set[UUID] = set()
                queue = deque([t_id])

                while queue:
                    curr = queue.popleft()
                    for p_id in dependent_to_prereqs_id.get(curr, []):
                        if p_id not in visited_upstream:
                            visited_upstream.add(p_id)
                            queue.append(p_id)
                            # Check if p_id is unacquired and not explicitly a target skill
                            is_sat = p_id in satisfied_skill_ids
                            if not is_sat and p_id not in target_skill_ids:
                                implicit_prerequisites.setdefault(p_id, set()).add(t_id)

        # 7. Collect All Evaluated Skills (Path Items + Explicit Target Skills + Implicit Prerequisites if enabled)
        evaluated_skill_ids: Set[UUID] = set(target_skill_ids)
        for item in path.items:
            evaluated_skill_ids.add(item.skill_id)
        if include_implicit:
            for imp_id in implicit_prerequisites.keys():
                evaluated_skill_ids.add(imp_id)

        # Pre-index path items by skill_id
        item_by_skill_id: Dict[UUID, LearningPathItem] = {
            item.skill_id: item for item in path.items
        }

        # Pre-index match statuses by skill_id / skill_name
        match_status_by_id: Dict[UUID, str] = {}
        match_status_by_name: Dict[str, str] = {}
        if match_analysis:
            for sm in match_analysis.skill_matches:
                if sm.canonical_skill_id:
                    match_status_by_id[sm.canonical_skill_id] = sm.match_status
                if sm.canonical_skill_name:
                    match_status_by_name[sm.canonical_skill_name.lower().strip()] = sm.match_status

        # 8. Compute Prioritization Metrics for Each Evaluated Skill
        prioritized_skills: List[PrioritizedSkillSchema] = []

        for s_id in evaluated_skill_ids:
            skill_obj = all_skill_lookup.get(s_id)
            if not skill_obj:
                skill_obj = self.db.query(Skill).filter(Skill.id == s_id).first()
                if skill_obj:
                    all_skill_lookup[s_id] = skill_obj

            skill_name = skill_obj.name if skill_obj else "Unknown Skill"
            skill_cat = skill_obj.category if skill_obj else "TECHNICAL_SKILL"
            item = item_by_skill_id.get(s_id)
            item_status = item.status if item else "NOT_STARTED"
            stage_order = item.stage_order if item else None

            # Determine estimated hours with strict precedence:
            # 1. item.estimated_hours
            # 2. resource.estimated_hours
            # 3. fallback 6.0
            # Clamped to [4.0, 40.0]
            if item and item.estimated_hours and item.estimated_hours > 0:
                raw_h = item.estimated_hours
            elif item and item.resource and item.resource.estimated_hours > 0:
                raw_h = item.resource.estimated_hours
            else:
                raw_h = FALLBACK_HOURS
            hours = clamp_learning_hours(raw_h)

            is_implicit = s_id in implicit_prerequisites and s_id not in target_skill_ids

            # A. Role Criticality (RC)
            if is_implicit:
                dep_targets = implicit_prerequisites[s_id]
                dep_criticalities = []
                for dt_id in dep_targets:
                    t_info = target_skills_dict.get(dt_id, {})
                    dep_req = t_info.get("requirement_type", "REQUIRED")
                    dep_wt = t_info.get("importance_weight", 1.0)
                    dep_criticalities.append(
                        calculate_role_criticality(
                            requirement_type=dep_req,
                            importance_weight=dep_wt,
                            is_implicit_prerequisite=False,
                        )
                    )
                rc = calculate_role_criticality(
                    is_implicit_prerequisite=True,
                    dependent_criticalities=dep_criticalities,
                )
            else:
                t_info = target_skills_dict.get(s_id, {})
                req_type = t_info.get("requirement_type", "REQUIRED")
                imp_wt = t_info.get("importance_weight", 1.0)
                rc = calculate_role_criticality(
                    requirement_type=req_type,
                    importance_weight=imp_wt,
                    is_implicit_prerequisite=False,
                )

            # B. Gap Impact (GI)
            g_status = match_status_by_id.get(s_id) or match_status_by_name.get(skill_name.lower().strip())
            if not g_status:
                if s_id in satisfied_skill_ids or skill_name.lower().strip() in satisfied_skill_names:
                    g_status = "MATCHED_REQUIRED"
                else:
                    g_status = "MISSING_REQUIRED" if rc >= 75.0 else "MISSING_PREFERRED"
            gi = calculate_gap_impact(match_status=g_status)

            # C. Dependency Leverage (DL) via multi-hop BFS
            # Find reachable unacquired target skills
            unlocked_target_ids = find_downstream_unlocked_skills(
                skill_key=s_id,
                prereq_to_dependents=prereq_to_dependents_id,
                target_skill_keys=target_skill_ids,
                satisfied_skill_keys=satisfied_skill_ids,
            )
            downstream_count = len(unlocked_target_ids)
            dl = calculate_dependency_leverage(unlocked_count=downstream_count)

            downstream_names = [
                all_skill_lookup[dt_id].name
                for dt_id in unlocked_target_ids
                if dt_id in all_skill_lookup
            ]

            # D. Learning Efficiency (LE) via in-memory delta simulation
            delta_compat = 0.0
            is_already_acquired = (
                s_id in satisfied_skill_ids
                or skill_name.lower().strip() in satisfied_skill_names
                or item_status == "COMPLETED"
            )

            if match_analysis and not is_already_acquired and path.target_type == "JOB":
                delta_compat = self._simulate_skill_acquisition_delta(
                    match_analysis=match_analysis,
                    skill_id=s_id,
                    skill_name=skill_name,
                    alignment_dict=alignment_dict,
                )

            le = calculate_learning_efficiency(
                delta_compatibility=delta_compat,
                estimated_hours=hours,
            )

            # E. Combined Priority Score
            score = calculate_priority_score(
                role_criticality=rc,
                dependency_leverage=dl,
                gap_impact=gi,
                learning_efficiency=le,
            )

            # F. Readiness Hard Gatekeeper
            direct_prereqs_ids = dependent_to_prereqs_id.get(s_id, [])
            readiness, unsatisfied_ids, satisfied_ids = evaluate_readiness(
                skill_key=s_id,
                direct_prerequisites=direct_prereqs_ids,
                satisfied_skill_keys=satisfied_skill_ids,
                is_already_completed=is_already_acquired,
            )

            unsatisfied_names = [
                all_skill_lookup[p].name for p in unsatisfied_ids if p in all_skill_lookup
            ]
            satisfied_names = [
                all_skill_lookup[p].name for p in satisfied_ids if p in all_skill_lookup
            ]

            # G. Deterministic Explanation
            explanation = generate_deterministic_explanation(
                skill_name=skill_name,
                readiness_status=readiness,
                priority_score=score,
                role_criticality=rc,
                downstream_unlocked_count=downstream_count,
                downstream_unlocked_names=downstream_names,
                estimated_hours=hours,
                delta_compatibility=delta_compat,
                unsatisfied_prerequisites=unsatisfied_names,
                is_implicit_prerequisite=is_implicit,
            )

            prioritized_skills.append(
                PrioritizedSkillSchema(
                    skill_id=s_id,
                    skill_name=skill_name,
                    category=skill_cat,
                    priority_score=score,
                    role_criticality=rc,
                    dependency_leverage=dl,
                    gap_impact=gi,
                    learning_efficiency=le,
                    readiness_status=readiness,
                    unsatisfied_prerequisites=unsatisfied_names,
                    satisfied_prerequisites=satisfied_names,
                    downstream_unlocked_skills=downstream_names,
                    downstream_unlocked_count=downstream_count,
                    estimated_hours=hours,
                    delta_compatibility=delta_compat,
                    is_implicit_prerequisite=is_implicit,
                    explanation=explanation,
                    item_id=item.id if item else None,
                    status=item_status,
                    stage_order=stage_order,
                )
            )

        # 9. Sort Prioritized Skills via Cascade
        raw_dicts = [s.model_dump() for s in prioritized_skills]
        sorted_dicts = sort_prioritized_skills(raw_dicts)
        sorted_schemas = [PrioritizedSkillSchema.model_validate(d) for d in sorted_dicts]

        # 10. Select Next Best Skill (Must be READY and NOT COMPLETED)
        next_best_dict = select_next_best_skill(sorted_dicts)
        next_best_schema = None
        if next_best_dict:
            next_best_schema = NextBestSkillSchema(
                skill_id=next_best_dict["skill_id"],
                skill_name=next_best_dict["skill_name"],
                category=next_best_dict["category"],
                priority_score=next_best_dict["priority_score"],
                estimated_hours=next_best_dict["estimated_hours"],
                delta_compatibility=next_best_dict["delta_compatibility"],
                downstream_unlocked_count=next_best_dict["downstream_unlocked_count"],
                downstream_unlocked_skills=next_best_dict["downstream_unlocked_skills"],
                explanation=next_best_dict["explanation"],
                is_implicit_prerequisite=next_best_dict["is_implicit_prerequisite"],
                item_id=next_best_dict.get("item_id"),
            )

        # 11. Calculate Counts
        total_count = len(sorted_schemas)
        ready_count = sum(1 for s in sorted_schemas if s.readiness_status == "READY")
        blocked_count = sum(1 for s in sorted_schemas if s.readiness_status == "BLOCKED")
        completed_count = sum(1 for s in sorted_schemas if s.readiness_status == "COMPLETED")

        # Determine Target Title
        target_title = None
        if path.target_type == "JOB" and path.job:
            target_title = path.job.title
        elif path.target_type == "CAREER" and path.occupation:
            target_title = path.occupation.title

        return PrioritizedRoadmapResponse(
            learning_path_id=path.id,
            target_type=path.target_type,
            target_title=target_title,
            overall_progress_percentage=path.overall_progress_percentage,
            total_skills_count=total_count,
            ready_skills_count=ready_count,
            blocked_skills_count=blocked_count,
            completed_skills_count=completed_count,
            next_best_skill=next_best_schema,
            prioritized_skills=sorted_schemas,
            diagnostics=diagnostic_cycles,
        )

    def _simulate_skill_acquisition_delta(
        self,
        match_analysis: MatchAnalysis,
        skill_id: UUID,
        skill_name: str,
        alignment_dict: Dict[str, Any],
    ) -> float:
        """
        Fast in-memory counterfactual simulation of acquiring a single skill.
        Calculates projected compatibility score using Phase 5 ScoringEngine.
        Returns compatibility delta bounded >= 0.0.
        """
        skill_name_lower = skill_name.lower().strip()
        projected_matches = []
        found_target_gap = False

        for m in match_analysis.skill_matches:
            is_match_target = (
                m.canonical_skill_id == skill_id
                or m.canonical_skill_name.lower().strip() == skill_name_lower
            )
            is_gap_status = (
                m.match_status.startswith("MISSING")
                or m.match_status.startswith("PARTIAL")
                or m.match_status == "UNCERTAIN"
                or m.match_status == "RELATED_SUPPORT"
            )

            if is_match_target and is_gap_status:
                found_target_gap = True
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
                    "resume_evidence": f"[Simulated Acquisition] Demonstrated mastery in {skill_name}.",
                    "job_evidence": m.job_evidence,
                    "explanation": f"Simulated: Fulfills '{m.canonical_skill_name}' requirement.",
                })
            else:
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

        if not found_target_gap:
            return 0.0

        scoring_res = ScoringEngine.calculate_scores(projected_matches, alignment_dict)
        projected_compatibility = scoring_res["compatibility_score"]
        delta = round(projected_compatibility - match_analysis.compatibility_score, 2)
        return max(0.0, delta)
