"""Learning service for generating, querying, and updating personalized learning paths."""

import uuid
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.resume import Resume
from app.models.career import Occupation
from app.models.job import Job
from app.models.skill import Skill
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
