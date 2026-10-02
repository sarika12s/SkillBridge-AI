"""Learning service for generating, querying, and updating personalized learning paths."""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.resume import Resume
from app.models.career import Occupation
from app.models.job import Job
from app.models.skill import Skill, ResumeSkill
from app.models.learning import LearningPath, LearningPathItem, LearningResource
from app.schemas.learning import (
    LearningPathCreateRequest,
    LearningPathResponseSchema,
    LearningStageSchema,
    LearningPathItemSchema,
    LearningResourceSchema,
    LearningPathGraphSchema,
    LearningPathGraphNode,
    LearningPathGraphEdge,
    ReconciliationRequest,
    ReconciliationResponse,
    VerifiedItemDetail,
)
from app.ai.learning.learning_engine import LearningEngine, STAGE_METADATA
from app.ai.learning.dependency_graph import SkillDependencyGraph


class LearningService:
    def __init__(self, db: Session):
        self.db = db
        self.engine = LearningEngine(db=db)
        self.graph = SkillDependencyGraph(db=db)

    def create_learning_path(
        self,
        user_id: uuid.UUID,
        req: LearningPathCreateRequest,
    ) -> LearningPathResponseSchema:
        """Creates a personalized learning path targeting a Career role or a Job."""
        resume = (
            self.db.query(Resume)
            .filter(Resume.id == req.resume_id, Resume.user_id == user_id)
            .first()
        )
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or access denied.",
            )

        if req.target_type == "CAREER":
            if not req.target_occupation_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="target_occupation_id is required for CAREER target_type.",
                )
            occ = (
                self.db.query(Occupation)
                .filter(Occupation.id == req.target_occupation_id)
                .first()
            )
            if not occ:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target occupation not found.",
                )
            path_obj = self.engine.generate_career_learning_path(
                resume=resume,
                occupation=occ,
                user_id=user_id,
            )

        elif req.target_type == "JOB":
            if not req.target_job_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="target_job_id is required for JOB target_type.",
                )
            job = (
                self.db.query(Job)
                .filter(Job.id == req.target_job_id, Job.user_id == user_id)
                .first()
            )
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target job not found or access denied.",
                )
            path_obj = self.engine.generate_job_learning_path(
                resume=resume,
                job=job,
                user_id=user_id,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid target_type. Must be CAREER or JOB.",
            )

        self.db.add(path_obj)
        self.db.commit()
        self.db.refresh(path_obj)

        return self.get_learning_path(path_obj.id, user_id)

    def get_learning_path(
        self,
        path_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> LearningPathResponseSchema:
        """Fetches learning path with items, organized stages, and interactive DAG representation."""
        path = (
            self.db.query(LearningPath)
            .options(
                joinedload(LearningPath.items).joinedload(LearningPathItem.skill),
                joinedload(LearningPath.items).joinedload(LearningPathItem.resource),
                joinedload(LearningPath.items).joinedload(LearningPathItem.verified_by_resume),
                joinedload(LearningPath.occupation),
                joinedload(LearningPath.job),
            )
            .filter(LearningPath.id == path_id, LearningPath.user_id == user_id)
            .first()
        )
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning path not found or access denied.",
            )

        # Group items into stages
        stages_dict: Dict[int, List[LearningPathItemSchema]] = {}
        for it in sorted(path.items, key=lambda x: (x.stage_order, x.sequence_in_stage)):
            res_schema = None
            if it.resource:
                res_schema = LearningResourceSchema(
                    id=it.resource.id,
                    skill_id=it.resource.skill_id,
                    skill_name=it.skill.name if it.skill else "",
                    title=it.resource.title,
                    provider=it.resource.provider,
                    url=it.resource.url,
                    resource_type=it.resource.resource_type,
                    cost_type=it.resource.cost_type,
                    difficulty_level=it.resource.difficulty_level,
                    estimated_hours=it.resource.estimated_hours,
                    description=it.resource.description,
                    rating=it.resource.rating,
                )

            item_schema = LearningPathItemSchema(
                id=it.id,
                learning_path_id=it.learning_path_id,
                skill_id=it.skill_id,
                skill_name=it.skill.name if it.skill else "Skill",
                skill_category=it.skill.category if it.skill else "TECHNICAL_SKILL",
                stage_order=it.stage_order,
                sequence_in_stage=it.sequence_in_stage,
                status=it.status,
                estimated_hours=it.estimated_hours,
                completed_at=it.completed_at,
                notes=it.notes,
                prerequisites_summary=it.prerequisites_summary,
                verified_by_resume_id=it.verified_by_resume_id,
                verified_by_resume_version=it.verified_by_resume.version if it.verified_by_resume else None,
                verified_at=it.verified_at,
                verification_method=it.verification_method,
                resource=res_schema,
            )

            if it.stage_order not in stages_dict:
                stages_dict[it.stage_order] = []
            stages_dict[it.stage_order].append(item_schema)

        stages_list = []
        for stage_order in sorted(stages_dict.keys()):
            items = stages_dict[stage_order]
            meta = STAGE_METADATA.get(
                stage_order,
                {
                    "title": f"Stage {stage_order} Competency Development",
                    "description": "Progressive skill acquisition and practical proficiency.",
                },
            )
            stage_hours = sum(it.estimated_hours for it in items)
            stages_list.append(
                LearningStageSchema(
                    stage_number=stage_order,
                    stage_title=meta["title"],
                    stage_description=meta["description"],
                    stage_estimated_hours=stage_hours,
                    items=items,
                )
            )

        # Build Graph Schema for Visualizer
        graph_nodes = []
        graph_edges = []
        node_ids = set()

        for it in path.items:
            sk_name = it.skill.name if it.skill else "Skill"
            graph_nodes.append(
                LearningPathGraphNode(
                    id=sk_name,
                    label=sk_name,
                    status=it.status,
                    category=it.skill.category if it.skill else None,
                    stage=it.stage_order,
                )
            )
            node_ids.add(sk_name)

        # Connect edges based on prerequisites
        for it in path.items:
            sk_name = it.skill.name if it.skill else "Skill"
            prereqs = self.graph.get_prerequisites_for_skill(sk_name)
            for p in prereqs:
                if p in node_ids:
                    graph_edges.append(
                        LearningPathGraphEdge(
                            source=p,
                            target=sk_name,
                            relationship_type="PREREQUISITE_OF",
                        )
                    )

        target_title = None
        if path.target_type == "CAREER" and path.occupation:
            target_title = path.occupation.title
        elif path.target_type == "JOB" and path.job:
            target_title = path.job.title

        return LearningPathResponseSchema(
            id=path.id,
            user_id=path.user_id,
            resume_id=path.resume_id,
            target_type=path.target_type,
            target_occupation_id=path.target_occupation_id,
            target_job_id=path.target_job_id,
            target_title=target_title,
            title=path.title,
            description=path.description,
            total_estimated_hours_min=path.total_estimated_hours_min,
            total_estimated_hours_max=path.total_estimated_hours_max,
            status=path.status,
            overall_progress_percentage=path.overall_progress_percentage,
            stages=stages_list,
            graph=LearningPathGraphSchema(nodes=graph_nodes, edges=graph_edges),
            created_at=path.created_at,
            updated_at=path.updated_at,
        )

    def get_user_learning_paths(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Lists summary of all learning paths belonging to the user."""
        paths = (
            self.db.query(LearningPath)
            .filter(LearningPath.user_id == user_id)
            .order_by(LearningPath.created_at.desc())
            .all()
        )
        results = []
        for p in paths:
            results.append({
                "id": p.id,
                "title": p.title,
                "target_type": p.target_type,
                "status": p.status,
                "overall_progress_percentage": p.overall_progress_percentage,
                "total_estimated_hours_min": p.total_estimated_hours_min,
                "total_estimated_hours_max": p.total_estimated_hours_max,
                "items_count": len(p.items),
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            })
        return results

    def update_item_progress(
        self,
        item_id: uuid.UUID,
        user_id: uuid.UUID,
        new_status: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Updates progress of a specific learning path item and recalculates overall path progress."""
        item = (
            self.db.query(LearningPathItem)
            .join(LearningPath)
            .filter(LearningPathItem.id == item_id, LearningPath.user_id == user_id)
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning path item not found or access denied.",
            )

        self.engine.update_item_progress(item, new_status, notes)
        self.db.commit()

        return {
            "item_id": item.id,
            "status": item.status,
            "completed_at": item.completed_at,
            "path_id": item.learning_path_id,
            "overall_progress_percentage": item.learning_path.overall_progress_percentage,
            "path_status": item.learning_path.status,
        }

    def reconcile_learning_path(
        self,
        path_id: uuid.UUID,
        user_id: uuid.UUID,
        req: Optional[ReconciliationRequest] = None,
    ) -> ReconciliationResponse:
        """
        Reconciles a candidate's active learning path against a newer resume version.
        Automatically verifies matching milestones if authoritative evidence exists.
        Monotonic: completed items are never demoted.
        Idempotent: running multiple times does not produce duplicate updates.
        """
        path = (
            self.db.query(LearningPath)
            .options(
                joinedload(LearningPath.items).joinedload(LearningPathItem.skill),
                joinedload(LearningPath.items).joinedload(LearningPathItem.verified_by_resume),
            )
            .filter(LearningPath.id == path_id, LearningPath.user_id == user_id)
            .first()
        )
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning path not found or access denied.",
            )

        baseline_resume = (
            self.db.query(Resume)
            .filter(Resume.id == path.resume_id)
            .first()
        )

        verifying_resume: Optional[Resume] = None
        if req and req.resume_id:
            verifying_resume = (
                self.db.query(Resume)
                .filter(Resume.id == req.resume_id)
                .first()
            )
            if not verifying_resume or verifying_resume.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Specified resume not found or access denied.",
                )
            if baseline_resume and verifying_resume.version < baseline_resume.version:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot reconcile roadmap against an older resume version (v{verifying_resume.version} < baseline v{baseline_resume.version}).",
                )
        else:
            # Pick the candidate's latest resume version
            verifying_resume = (
                self.db.query(Resume)
                .filter(Resume.user_id == user_id)
                .order_by(Resume.version.desc(), Resume.created_at.desc())
                .first()
            )
            if not verifying_resume:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No resume found for candidate.",
                )

        baseline_id = baseline_resume.id if baseline_resume else path.resume_id
        items_evaluated = len(path.items)
        previous_progress = path.overall_progress_percentage
        previous_remaining_hours = sum(
            it.estimated_hours for it in path.items if it.status != "COMPLETED"
        )
        already_completed_count = sum(
            1 for it in path.items if it.status == "COMPLETED"
        )

        # Fetch candidate skills from verifying resume
        resume_skills = (
            self.db.query(ResumeSkill)
            .filter(ResumeSkill.resume_id == verifying_resume.id)
            .all()
        )

        # Filter qualified skills:
        # 1. match_method in ("EXACT", "ALIAS") with confidence >= 0.90, or "LEXICON_MATCH" with confidence >= 0.85
        # 2. evidence_sentence with length >= 10 chars
        # 3. SEMANTIC_EMBEDDING strictly disqualified
        qualified_skills: Dict[uuid.UUID, ResumeSkill] = {}
        qualified_by_name: Dict[str, ResumeSkill] = {}

        for rs in resume_skills:
            if not rs.evidence_sentence or len(rs.evidence_sentence.strip()) < 10:
                continue
            is_valid = False
            if rs.match_method in ("EXACT", "ALIAS") and rs.confidence >= 0.90:
                is_valid = True
            elif rs.match_method == "LEXICON_MATCH" and rs.confidence >= 0.85:
                is_valid = True

            if is_valid:
                # Keep highest confidence if duplicate skill mentions
                if rs.skill_id and (
                    rs.skill_id not in qualified_skills
                    or rs.confidence > qualified_skills[rs.skill_id].confidence
                ):
                    qualified_skills[rs.skill_id] = rs
                if rs.canonical_skill_name:
                    norm_key = rs.canonical_skill_name.lower().strip()
                    if (
                        norm_key not in qualified_by_name
                        or rs.confidence > qualified_by_name[norm_key].confidence
                    ):
                        qualified_by_name[norm_key] = rs

        newly_verified_items: List[VerifiedItemDetail] = []
        now_dt = datetime.now(timezone.utc)

        # Iterate over items in path
        for item in path.items:
            # Monotonicity rule: never demote or alter already COMPLETED items
            if item.status == "COMPLETED":
                continue

            # Check if skill matches qualified skills
            matched_rs = None
            if item.skill_id:
                matched_rs = qualified_skills.get(item.skill_id)
            if not matched_rs and item.skill and item.skill.name:
                matched_rs = qualified_by_name.get(item.skill.name.lower().strip())

            if matched_rs:
                item.status = "COMPLETED"
                item.completed_at = now_dt
                item.verified_by_resume_id = verifying_resume.id
                item.verified_at = now_dt
                item.verification_method = "RESUME_EVIDENCE"
                item.verified_by_resume = verifying_resume

                note_msg = (
                    f"Auto-verified by Resume v{verifying_resume.version} ({verifying_resume.file_name}) "
                    f"via {matched_rs.match_method} (confidence {matched_rs.confidence:.2f}): "
                    f"\"{matched_rs.evidence_sentence}\""
                )
                if item.notes:
                    item.notes = f"{item.notes}\n{note_msg}"
                else:
                    item.notes = note_msg

                newly_verified_items.append(
                    VerifiedItemDetail(
                        item_id=item.id,
                        skill_id=item.skill_id,
                        skill_name=item.skill.name if item.skill else "Skill",
                        stage_order=item.stage_order,
                        match_method=matched_rs.match_method,
                        confidence=matched_rs.confidence,
                        evidence_sentence=matched_rs.evidence_sentence,
                        verified_at=now_dt,
                    )
                )

        # Recalculate roadmap progress
        new_completed_count = sum(1 for it in path.items if it.status == "COMPLETED")
        new_progress = (
            round((new_completed_count / items_evaluated) * 100.0, 1)
            if items_evaluated > 0
            else 0.0
        )
        new_remaining_hours = sum(
            it.estimated_hours for it in path.items if it.status != "COMPLETED"
        )
        remaining_unverified = items_evaluated - new_completed_count

        path.overall_progress_percentage = new_progress
        if new_progress >= 100.0:
            path.status = "COMPLETED"
        elif new_progress > 0.0:
            path.status = "IN_PROGRESS"
        path.updated_at = now_dt

        self.db.commit()
        self.db.refresh(path)

        if len(newly_verified_items) > 0:
            msg = (
                f"Successfully reconciled learning path with Resume v{verifying_resume.version}. "
                f"Auto-verified {len(newly_verified_items)} milestone(s). "
                f"Progress updated from {previous_progress}% to {new_progress}%."
            )
        else:
            msg = (
                f"Reconciliation evaluated {items_evaluated} milestone(s) against Resume v{verifying_resume.version}. "
                f"No new matching authoritative skill evidence was found."
            )

        return ReconciliationResponse(
            learning_path_id=path.id,
            baseline_resume_id=baseline_id,
            verifying_resume_id=verifying_resume.id,
            verifying_resume_version=verifying_resume.version,
            items_evaluated=items_evaluated,
            newly_verified_count=len(newly_verified_items),
            already_completed_count=already_completed_count,
            remaining_unverified_count=remaining_unverified,
            previous_progress_percentage=previous_progress,
            new_progress_percentage=new_progress,
            previous_remaining_hours=previous_remaining_hours,
            new_remaining_hours=new_remaining_hours,
            path_status=path.status,
            verified_items=newly_verified_items,
            message=msg,
        )
