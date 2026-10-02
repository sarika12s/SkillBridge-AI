"""Personalized Learning Path Recommendation Engine.

Generates prerequisite-aware, staged learning paths for Career and Job targets.
Associates real, curated resources and tracks modular learning progress.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.career import Occupation
from app.models.job import Job
from app.models.skill import Skill
from app.models.learning import LearningPath, LearningPathItem, LearningResource
from app.ai.learning.dependency_graph import SkillDependencyGraph


STAGE_METADATA = {
    1: {
        "title": "Foundational Competencies & Prerequisites",
        "description": "Establish core language semantics, fundamentals, and base environment tools.",
    },
    2: {
        "title": "Core Technologies & Practical Frameworks",
        "description": "Master primary production frameworks, relational persistence, and practical application patterns.",
    },
    3: {
        "title": "Advanced Architectures & Production Ecosystem",
        "description": "Scale up with distributed infrastructure, container orchestration, caching, and specialized libraries.",
    },
    4: {
        "title": "Specialized Mastery & Cloud Integration",
        "description": "Refine advanced domain patterns, automated pipelines, and cloud ecosystem services.",
    },
}


class LearningEngine:
    """Orchestrates personalized learning path generation and progress re-evaluation."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.graph = SkillDependencyGraph(db=db)

    def generate_career_learning_path(
        self,
        resume: Resume,
        occupation: Occupation,
        user_id: Any,
    ) -> LearningPath:
        """Generates a personalized learning path targeting a standardized career occupation."""
        # 1. Collect target skills from occupation
        target_skills = []
        for os in getattr(occupation, "skills", []):
            sk_name = os.skill.name if getattr(os, "skill", None) else None
            if sk_name and sk_name not in target_skills:
                target_skills.append(sk_name)

        # 2. Collect candidate's acquired skills
        acquired_skills = self._get_acquired_skills(resume)

        # 3. Compute staged DAG
        staged_plan = self.graph.organize_learning_stages(target_skills, acquired_skills)
        stages = staged_plan["stages"]

        # 4. Construct LearningPath model
        path = LearningPath(
            user_id=user_id,
            resume_id=resume.id,
            target_type="CAREER",
            target_occupation_id=occupation.id,
            title=f"Career Pathway: {occupation.title}",
            description=f"Prerequisite-aware personalized learning path to achieve full technical readiness as a {occupation.title}.",
            status="IN_PROGRESS",
            overall_progress_percentage=0.0,
        )

        # 5. Build items with resources and effort estimations
        total_hours = self._populate_path_items(path, stages, acquired_skills)
        path.total_estimated_hours_min = int(total_hours * 0.85)
        path.total_estimated_hours_max = int(total_hours * 1.25)

        return path

    def generate_job_learning_path(
        self,
        resume: Resume,
        job: Job,
        user_id: Any,
    ) -> LearningPath:
        """Generates a personalized learning path targeting a specific Job Description."""
        # 1. Collect target skills from Job
        target_skills = []
        for js in getattr(job, "skills", []):
            sk_name = js.skill.name if getattr(js, "skill", None) else js.raw_text
            if sk_name and sk_name not in target_skills:
                target_skills.append(sk_name)

        # 2. Collect candidate's acquired skills
        acquired_skills = self._get_acquired_skills(resume)

        # 3. Compute staged DAG
        staged_plan = self.graph.organize_learning_stages(target_skills, acquired_skills)
        stages = staged_plan["stages"]

        # 4. Construct LearningPath model
        job_title = job.title or "Target Role"
        company = f" at {job.company_name}" if getattr(job, "company_name", None) else ""
        path = LearningPath(
            user_id=user_id,
            resume_id=resume.id,
            target_type="JOB",
            target_job_id=job.id,
            title=f"Role Readiness: {job_title}{company}",
            description=f"Actionable roadmap bridging identified skill gaps for the {job_title} position.",
            status="IN_PROGRESS",
            overall_progress_percentage=0.0,
        )

        # 5. Build items
        total_hours = self._populate_path_items(path, stages, acquired_skills)
        path.total_estimated_hours_min = int(total_hours * 0.85)
        path.total_estimated_hours_max = int(total_hours * 1.25)

        return path

    def _get_acquired_skills(self, resume: Resume) -> Set[str]:
        """Extracts candidate's verified/demonstrated skills from resume."""
        acquired = set()
        for rs in getattr(resume, "skills", []):
            if getattr(rs, "canonical_skill_name", None):
                acquired.add(rs.canonical_skill_name)
            elif getattr(rs, "skill", None):
                acquired.add(rs.skill.name)
            elif getattr(rs, "raw_skill_text", None):
                acquired.add(rs.raw_skill_text)
            elif getattr(rs, "raw_text", None):
                acquired.add(rs.raw_text)
        return acquired

    def _populate_path_items(
        self,
        path: LearningPath,
        stages: Dict[int, List[str]],
        acquired_skills: Set[str],
    ) -> float:
        """Populates LearningPathItem rows across stages and attaches curated resources."""
        total_hours = 0.0

        for stage_num, skill_list in stages.items():
            for seq, sk_name in enumerate(skill_list, start=1):
                skill_obj = self._resolve_skill(sk_name)
                resource_obj = self._resolve_resource(skill_obj, sk_name)

                est_hours = resource_obj.estimated_hours if resource_obj else 6.0
                total_hours += est_hours

                # Prerequisites explanation
                prereqs = self.graph.get_prerequisites_for_skill(sk_name)
                if prereqs:
                    prereq_str = f"Prerequisites: {', '.join(prereqs)}"
                else:
                    prereq_str = "Foundational topic; no prior technical prerequisites required."

                item = LearningPathItem(
                    skill_id=skill_obj.id if skill_obj else None,
                    resource_id=resource_obj.id if resource_obj else None,
                    stage_order=stage_num,
                    sequence_in_stage=seq,
                    status="NOT_STARTED",
                    estimated_hours=est_hours,
                    prerequisites_summary=prereq_str,
                )
                if skill_obj:
                    item.skill = skill_obj
                if resource_obj:
                    item.resource = resource_obj

                path.items.append(item)

        return total_hours

    def _resolve_skill(self, name: str) -> Optional[Skill]:
        """Resolves Skill model from DB if available."""
        if self.db:
            sk = self.db.query(Skill).filter(Skill.name == name).first()
            if not sk:
                sk = self.db.query(Skill).filter(Skill.normalized_name == name.lower()).first()
            return sk
        return None

    def _resolve_resource(
        self,
        skill: Optional[Skill],
        skill_name: str,
    ) -> Optional[LearningResource]:
        """Finds matching curated LearningResource from database or fallback resource seed."""
        if self.db and skill:
            res = (
                self.db.query(LearningResource)
                .filter(LearningResource.skill_id == skill.id)
                .first()
            )
            if res:
                return res

        # Fallback from json
        json_file = (
            Path(__file__).resolve().parent.parent.parent
            / "data"
            / "resources"
            / "learning_resources.json"
        )
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        if item["skill_name"].lower() == skill_name.lower():
                            res_obj = LearningResource(
                                skill_id=skill.id if skill else None,
                                title=item["title"],
                                provider=item["provider"],
                                url=item["url"],
                                resource_type=item.get("resource_type", "DOCUMENTATION"),
                                cost_type=item.get("cost_type", "FREE"),
                                difficulty_level=item.get("difficulty_level", "BEGINNER"),
                                estimated_hours=float(item.get("estimated_hours", 5.0)),
                                description=item.get("description"),
                                rating=float(item.get("rating", 4.8)),
                            )
                            if self.db:
                                self.db.add(res_obj)
                            return res_obj
            except Exception:
                pass
        return None

    def update_item_progress(
        self,
        item: LearningPathItem,
        new_status: str,
        notes: Optional[str] = None,
    ) -> None:
        """
        Updates status of an individual item and re-evaluates parent path progress.
        Permitted statuses: NOT_STARTED, IN_PROGRESS, COMPLETED.
        """
        item.status = new_status
        if notes is not None:
            item.notes = notes

        if new_status == "COMPLETED":
            item.completed_at = datetime.now(timezone.utc)
        elif new_status == "NOT_STARTED":
            item.completed_at = None

        # Re-evaluate parent LearningPath
        if item.learning_path:
            all_items = item.learning_path.items
            if all_items:
                completed_count = sum(1 for it in all_items if it.status == "COMPLETED")
                progress = round((completed_count / len(all_items)) * 100.0, 1)
                item.learning_path.overall_progress_percentage = progress

                if progress >= 100.0:
                    item.learning_path.status = "COMPLETED"
                elif progress > 0.0:
                    item.learning_path.status = "IN_PROGRESS"
