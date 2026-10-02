"""Progress Tracking Service for Skills, Learning Roadmaps, and Analytical Scores."""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.resume import Resume
from app.models.skill import ResumeSkill
from app.models.matching import MatchAnalysis, SkillMatch
from app.models.career import CareerCompatibility
from app.models.learning import LearningPath, LearningPathItem
from app.schemas.dashboard import (
    SkillHistoryItem,
    SkillHistoryResponse,
    ScoreHistoryItem,
    LearningProgressOverview,
)


class ProgressService:
    def __init__(self, db: Session):
        self.db = db

    def get_skill_history(
        self, user_id: uuid.UUID, skill_name: Optional[str] = None
    ) -> List[SkillHistoryResponse]:
        """
        Analyzes the trajectory of skills across chronological resume versions for the user.
        Determines whether skills are FIRST_DETECTED, RETAINED, NEW, REMOVED, STRENGTHENED, or WEAKENED.
        """
        resumes = (
            self.db.query(Resume)
            .options(joinedload(Resume.skills).joinedload(ResumeSkill.skill))
            .filter(Resume.user_id == user_id)
            .order_by(Resume.version.asc(), Resume.created_at.asc())
            .all()
        )

        if not resumes:
            return []

        # Map resume_id to skills dict {clean_skill_name: ResumeSkill}
        version_skills: List[Dict[str, Any]] = []
        all_skill_canonical_names: Dict[str, str] = {}  # lower -> display name
        skill_categories: Dict[str, str] = {}

        for r in resumes:
            skills_dict: Dict[str, ResumeSkill] = {}
            for rs in (r.skills or []):
                name = (rs.canonical_skill_name or rs.raw_skill_text or "").strip()
                if not name:
                    continue
                name_key = name.lower()
                skills_dict[name_key] = rs
                all_skill_canonical_names[name_key] = name
                if name_key not in skill_categories:
                    cat = rs.skill.category if rs.skill and hasattr(rs.skill, 'category') and rs.skill.category else "TECHNICAL"
                    skill_categories[name_key] = cat
            version_skills.append({
                "resume": r,
                "skills": skills_dict,
            })

        # Track history per skill
        skill_timelines: Dict[str, List[SkillHistoryItem]] = {
            k: [] for k in all_skill_canonical_names.keys()
        }

        previous_skills: Dict[str, ResumeSkill] = {}
        for idx, entry in enumerate(version_skills):
            r = entry["resume"]
            current_skills: Dict[str, ResumeSkill] = entry["skills"]

            # Process all skills currently present
            for skill_key, rs in current_skills.items():
                section = (rs.source_section or "SKILLS").upper()
                evidence = rs.evidence_sentence or ""
                confidence = rs.confidence if rs.confidence is not None else 1.0

                if idx == 0:
                    status = "FIRST_DETECTED"
                else:
                    if skill_key not in previous_skills:
                        status = "NEW"
                    else:
                        prev_rs = previous_skills[skill_key]
                        prev_sec = (prev_rs.source_section or "SKILLS").upper()
                        # Strengthened criteria: moved to EXPERIENCE/PROJECTS from SKILLS/EDUCATION
                        is_strengthened = (
                            section in ["EXPERIENCE", "PROJECTS"]
                            and prev_sec not in ["EXPERIENCE", "PROJECTS"]
                        )
                        is_weakened = (
                            section not in ["EXPERIENCE", "PROJECTS"]
                            and prev_sec in ["EXPERIENCE", "PROJECTS"]
                        )
                        if is_strengthened:
                            status = "STRENGTHENED"
                        elif is_weakened:
                            status = "WEAKENED"
                        else:
                            status = "RETAINED"

                skill_timelines[skill_key].append(
                    SkillHistoryItem(
                        resume_id=r.id,
                        resume_version=r.version,
                        detected_at=r.created_at,
                        status=status,
                        evidence_sentence=evidence,
                        source_section=section,
                        confidence=confidence,
                    )
                )

            # Detect skills removed in this version (present in previous, not in current)
            if idx > 0:
                for skill_key, prev_rs in previous_skills.items():
                    if skill_key not in current_skills:
                        skill_timelines[skill_key].append(
                            SkillHistoryItem(
                                resume_id=r.id,
                                resume_version=r.version,
                                detected_at=r.created_at,
                                status="REMOVED",
                                evidence_sentence=None,
                                source_section=None,
                                confidence=0.0,
                            )
                        )

            previous_skills = current_skills

        # Build responses
        responses: List[SkillHistoryResponse] = []
        for skill_key, timeline in skill_timelines.items():
            disp_name = all_skill_canonical_names[skill_key]
            if skill_name and skill_name.lower() not in skill_key:
                continue

            current_status = timeline[-1].status if timeline else "UNKNOWN"
            responses.append(
                SkillHistoryResponse(
                    skill_name=disp_name,
                    category=skill_categories.get(skill_key, "TECHNICAL"),
                    current_status=current_status,
                    history=timeline,
                )
            )

        responses.sort(key=lambda s: s.skill_name.lower())
        return responses

    def get_learning_progress(self, user_id: uuid.UUID) -> LearningProgressOverview:
        """
        Aggregates learning path progress, module counts, and estimated completion hours.
        """
        paths = (
            self.db.query(LearningPath)
            .options(joinedload(LearningPath.items))
            .filter(LearningPath.user_id == user_id)
            .order_by(LearningPath.created_at.desc())
            .all()
        )

        if not paths:
            return LearningProgressOverview()

        total_paths = len(paths)
        completed_paths = sum(1 for p in paths if p.status == "COMPLETED")
        in_progress_paths = sum(1 for p in paths if p.status == "IN_PROGRESS")

        # Prioritize active in-progress path, fallback to latest path
        active_path = next((p for p in paths if p.status == "IN_PROGRESS"), paths[0])

        items = active_path.items or []
        total_items = len(items)
        completed_items = sum(1 for i in items if i.status == "COMPLETED")
        in_progress_items = sum(1 for i in items if i.status == "IN_PROGRESS")
        not_started_items = sum(1 for i in items if i.status == "NOT_STARTED")

        overall_pct = active_path.overall_progress_percentage
        if total_items > 0 and overall_pct == 0.0 and completed_items > 0:
            overall_pct = round((completed_items / total_items) * 100.0, 1)

        total_hours = sum(i.estimated_hours for i in items)
        remaining_hours = sum(
            i.estimated_hours for i in items if i.status != "COMPLETED"
        )

        # Determine current stage (stage of first incomplete item)
        incomplete_items = [i for i in items if i.status != "COMPLETED"]
        current_stage = (
            incomplete_items[0].stage_order if incomplete_items else 1
        )

        target_name = None
        if active_path.target_type == "CAREER" and active_path.occupation:
            target_name = active_path.occupation.title
        elif active_path.target_type == "JOB" and active_path.job:
            target_name = active_path.job.title

        return LearningProgressOverview(
            total_paths=total_paths,
            completed_paths=completed_paths,
            in_progress_paths=in_progress_paths,
            active_path_id=active_path.id,
            active_path_title=active_path.title,
            active_path_target=target_name,
            total_items=total_items,
            completed_items=completed_items,
            in_progress_items=in_progress_items,
            not_started_items=not_started_items,
            overall_completion_percentage=round(overall_pct, 1),
            total_estimated_hours=round(total_hours, 1),
            remaining_estimated_hours=round(remaining_hours, 1),
            current_stage=current_stage,
        )

    def get_score_history(self, user_id: uuid.UUID) -> List[ScoreHistoryItem]:
        """
        Gathers chronological history of ATS readiness, Job Compatibility, and Career scores.
        """
        # 1. Job Match Analyses
        matches = (
            self.db.query(MatchAnalysis)
            .options(
                joinedload(MatchAnalysis.resume),
                joinedload(MatchAnalysis.job),
                joinedload(MatchAnalysis.skill_matches),
            )
            .filter(MatchAnalysis.user_id == user_id)
            .order_by(MatchAnalysis.created_at.asc())
            .all()
        )

        history_items: List[ScoreHistoryItem] = []

        for m in matches:
            if not m.resume or not m.job:
                continue

            req_matches = [
                sm for sm in (m.skill_matches or []) if sm.priority == "REQUIRED"
            ]
            matched_req = [
                sm for sm in req_matches if sm.match_status.startswith("MATCHED")
            ]
            req_cov = (
                round((len(matched_req) / len(req_matches)) * 100, 1)
                if req_matches
                else None
            )

            pref_matches = [
                sm for sm in (m.skill_matches or []) if sm.priority == "PREFERRED"
            ]
            matched_pref = [
                sm for sm in pref_matches if sm.match_status.startswith("MATCHED")
            ]
            pref_cov = (
                round((len(matched_pref) / len(pref_matches)) * 100, 1)
                if pref_matches
                else None
            )

            history_items.append(
                ScoreHistoryItem(
                    analysis_id=m.id,
                    analysis_type="JOB_MATCH",
                    resume_id=m.resume_id,
                    resume_version=m.resume.version,
                    target_id=m.job_id,
                    target_title=m.job.title,
                    company_name=m.job.company,
                    ats_readiness_score=round(m.ats_readiness_score, 1),
                    compatibility_score=round(m.compatibility_score, 1),
                    required_skill_coverage=req_cov,
                    preferred_skill_coverage=pref_cov,
                    scoring_version=m.scoring_version,
                    engine_version=m.matching_engine_version,
                    created_at=m.created_at,
                )
            )

        # 2. Career Compatibility Analyses
        careers = (
            self.db.query(CareerCompatibility)
            .options(
                joinedload(CareerCompatibility.resume),
                joinedload(CareerCompatibility.occupation),
            )
            .filter(CareerCompatibility.user_id == user_id)
            .order_by(CareerCompatibility.created_at.asc())
            .all()
        )

        for c in careers:
            if not c.resume or not c.occupation:
                continue

            history_items.append(
                ScoreHistoryItem(
                    analysis_id=c.id,
                    analysis_type="CAREER_COMPATIBILITY",
                    resume_id=c.resume_id,
                    resume_version=c.resume.version,
                    target_id=c.occupation_id,
                    target_title=c.occupation.title,
                    company_name=None,
                    ats_readiness_score=None,
                    compatibility_score=round(c.compatibility_score, 1),
                    required_skill_coverage=None,
                    preferred_skill_coverage=None,
                    scoring_version=c.scoring_version,
                    engine_version=c.matching_engine_version,
                    created_at=c.created_at,
                )
            )

        history_items.sort(key=lambda x: x.created_at)
        return history_items
