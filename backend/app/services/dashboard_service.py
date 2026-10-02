"""Career Intelligence Dashboard Aggregation Service."""

import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.resume import Resume
from app.models.skill import ResumeSkill
from app.models.matching import MatchAnalysis, SkillMatch, SkillGap
from app.models.career import CareerCompatibility
from app.models.learning import LearningPath
from app.schemas.resume import ResumeSummaryResponse
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    LearningProgressOverview,
    ScoreHistoryItem,
)
from app.services.progress_service import ProgressService


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.progress_service = ProgressService(db)

    def get_dashboard_overview(self, user_id: uuid.UUID) -> DashboardOverviewResponse:
        """
        Aggregates career intelligence, resume health, matching metrics, and learning progress.
        Evaluates the user's lifecycle state across the 9 defined operational states:
        NEW_USER, NO_RESUME, RESUME_ONLY, RESUME_ANALYZED, JOB_ANALYZED, CAREER_ANALYZED,
        LEARNING_PATH_CREATED, ACTIVE_LEARNING, COMPLETED_LEARNING.
        """
        # 1. User Resumes
        resumes = (
            self.db.query(Resume)
            .options(joinedload(Resume.sections), joinedload(Resume.skills))
            .filter(Resume.user_id == user_id)
            .order_by(Resume.version.desc(), Resume.created_at.desc())
            .all()
        )
        resume_count = len(resumes)
        latest_resume_entity = resumes[0] if resumes else None

        latest_resume_summary = None
        if latest_resume_entity:
            latest_resume_summary = ResumeSummaryResponse(
                id=latest_resume_entity.id,
                user_id=latest_resume_entity.user_id,
                title=latest_resume_entity.title,
                file_name=latest_resume_entity.file_name,
                file_type=latest_resume_entity.file_type,
                file_size_bytes=latest_resume_entity.file_size_bytes,
                parsing_status=latest_resume_entity.parsing_status,
                extraction_method=latest_resume_entity.extraction_method,
                page_count=latest_resume_entity.page_count,
                character_count=latest_resume_entity.character_count,
                version=latest_resume_entity.version,
                parsed_at=latest_resume_entity.parsed_at,
                created_at=latest_resume_entity.created_at,
                sections_count=len(latest_resume_entity.sections) if latest_resume_entity.sections else 0,
            )

        # 2. Latest Job Match Analysis
        latest_match = (
            self.db.query(MatchAnalysis)
            .options(
                joinedload(MatchAnalysis.job),
                joinedload(MatchAnalysis.skill_matches),
                joinedload(MatchAnalysis.skill_gaps),
            )
            .filter(MatchAnalysis.user_id == user_id)
            .order_by(MatchAnalysis.created_at.desc())
            .first()
        )

        latest_job_analysis: Optional[Dict[str, Any]] = None
        latest_ats: Optional[float] = None
        latest_compat: Optional[float] = None
        req_coverage: Optional[float] = None
        pref_coverage: Optional[float] = None
        matched_count = 0
        missing_req_count = 0
        missing_pref_count = 0

        if latest_match:
            latest_ats = round(latest_match.ats_readiness_score, 1)
            latest_compat = round(latest_match.compatibility_score, 1)

            # Analyze skill matches and gaps
            matches = latest_match.skill_matches or []
            req_skills = [m for m in matches if m.priority == "REQUIRED"]
            pref_skills = [m for m in matches if m.priority == "PREFERRED"]

            matched_req = [m for m in req_skills if m.match_status.startswith("MATCHED")]
            matched_pref = [m for m in pref_skills if m.match_status.startswith("MATCHED")]

            if req_skills:
                req_coverage = round((len(matched_req) / len(req_skills)) * 100.0, 1)
            if pref_skills:
                pref_coverage = round((len(matched_pref) / len(pref_skills)) * 100.0, 1)

            matched_count = len(matched_req) + len(matched_pref)

            gaps = latest_match.skill_gaps or []
            missing_req_count = sum(1 for g in gaps if g.priority == "REQUIRED")
            missing_pref_count = sum(1 for g in gaps if g.priority == "PREFERRED")

            latest_job_analysis = {
                "id": str(latest_match.id),
                "job_id": str(latest_match.job_id),
                "job_title": latest_match.job.title if latest_match.job else "Target Role",
                "company_name": latest_match.job.company if latest_match.job else None,
                "compatibility_score": latest_compat,
                "ats_readiness_score": latest_ats,
                "scoring_version": latest_match.scoring_version,
                "created_at": latest_match.created_at.isoformat(),
            }

        # 3. Top Career Roles
        career_records = (
            self.db.query(CareerCompatibility)
            .options(joinedload(CareerCompatibility.occupation))
            .filter(CareerCompatibility.user_id == user_id)
            .order_by(CareerCompatibility.compatibility_score.desc())
            .limit(5)
            .all()
        )

        top_career_roles = []
        for c in career_records:
            if not c.occupation:
                continue
            top_career_roles.append({
                "id": str(c.id),
                "occupation_id": str(c.occupation_id),
                "title": c.occupation.title,
                "code": c.occupation.code,
                "category": c.occupation.category,
                "compatibility_score": round(c.compatibility_score, 1),
                "created_at": c.created_at.isoformat(),
            })

        # 4. Learning Progress
        learning_overview: LearningProgressOverview = self.progress_service.get_learning_progress(user_id)

        # 5. Score Trends
        score_trends: List[ScoreHistoryItem] = self.progress_service.get_score_history(user_id)

        # 6. Skill Gap Trends (Frequency / Criticality aggregated from match analyses)
        recent_gaps = (
            self.db.query(SkillGap)
            .join(MatchAnalysis)
            .filter(MatchAnalysis.user_id == user_id)
            .order_by(SkillGap.created_at.desc())
            .limit(10)
            .all()
        )
        skill_gap_trends = []
        for g in recent_gaps:
            skill_gap_trends.append({
                "id": str(g.id),
                "skill_name": g.canonical_skill_name,
                "priority": g.priority,
                "importance_weight": round(g.importance_weight, 2),
                "difficulty_level": getattr(g, "difficulty_level", "INTERMEDIATE") or "INTERMEDIATE",
                "reason": g.explanation,
            })

        # 7. Evaluate Operational Lifecycle State
        state = "NEW_USER"
        if resume_count == 0:
            state = "NO_RESUME"
        else:
            # Has at least one resume
            state = "RESUME_ONLY"
            if latest_match:
                state = "RESUME_ANALYZED"
            elif career_records:
                state = "CAREER_ANALYZED"

            if learning_overview.total_paths > 0:
                if learning_overview.completed_items == learning_overview.total_items and learning_overview.total_items > 0:
                    state = "COMPLETED_LEARNING"
                elif learning_overview.completed_items > 0 or learning_overview.in_progress_items > 0:
                    state = "ACTIVE_LEARNING"
                else:
                    state = "LEARNING_PATH_CREATED"

        # 8. Generate Rule-Based Explainable Insights
        insights: List[str] = []
        if latest_resume_summary:
            insights.append(
                f"Active Resume: '{latest_resume_summary.title}' (v{latest_resume_summary.version}) with "
                f"{latest_resume_summary.sections_count} structured sections analyzed."
            )

        if latest_match:
            insights.append(
                f"ATS Readiness is {latest_ats}% for '{latest_job_analysis['job_title']}'. "
                f"You matched {matched_count} target skills with {req_coverage or 0.0}% required coverage."
            )
            if missing_req_count > 0:
                critical_gaps = [g['skill_name'] for g in skill_gap_trends if g['priority'] == 'REQUIRED'][:3]
                if critical_gaps:
                    insights.append(
                        f"Top required skill gaps to close: {', '.join(critical_gaps)}."
                    )

        if top_career_roles:
            best_role = top_career_roles[0]
            insights.append(
                f"Highest career role alignment: '{best_role['title']}' with {best_role['compatibility_score']}% fit."
            )

        if learning_overview.active_path_title:
            insights.append(
                f"Learning roadmap active: {learning_overview.completed_items}/{learning_overview.total_items} modules "
                f"completed ({learning_overview.overall_completion_percentage}%). "
                f"{learning_overview.remaining_estimated_hours}h estimated work remaining."
            )

        if not insights:
            insights.append("Welcome to SkillBridge AI! Upload your resume to start receiving explainable career intelligence.")

        return DashboardOverviewResponse(
            state=state,
            latest_resume=latest_resume_summary,
            resume_versions_count=resume_count,
            latest_job_analysis=latest_job_analysis,
            latest_ats_readiness_score=latest_ats,
            latest_job_compatibility_score=latest_compat,
            required_skill_coverage=req_coverage,
            preferred_skill_coverage=pref_coverage,
            matched_skills_count=matched_count,
            missing_required_skills_count=missing_req_count,
            missing_preferred_skills_count=missing_pref_count,
            top_career_roles=top_career_roles,
            learning_overview=learning_overview,
            score_trends=score_trends,
            skill_gap_trends=skill_gap_trends,
            insights=insights,
        )
