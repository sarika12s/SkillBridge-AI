"""Career role service for managing occupations and computing multi-role compatibility."""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.resume import Resume
from app.models.career import (
    Occupation,
    OccupationSkill,
    CareerCompatibility,
    CareerCompatibilityComponent,
)
from app.schemas.career import (
    OccupationResponseSchema,
    CareerCompatibilityResponseSchema,
    CareerRoleMatchSchema,
    CareerCompatibilityComponentSchema,
)
from app.ai.career.career_engine import CareerEngine


class CareerService:
    def __init__(self, db: Session):
        self.db = db
        self.engine = CareerEngine(db=db)

    def get_all_occupations(self) -> List[Occupation]:
        """Returns all standardized occupations with preloaded skills."""
        return (
            self.db.query(Occupation)
            .options(joinedload(Occupation.skills).joinedload(OccupationSkill.skill))
            .all()
        )

    def get_occupation_by_id(self, occupation_id: uuid.UUID) -> Optional[Occupation]:
        """Returns a single occupation by ID or 404."""
        occ = (
            self.db.query(Occupation)
            .options(joinedload(Occupation.skills).joinedload(OccupationSkill.skill))
            .filter(Occupation.id == occupation_id)
            .first()
        )
        if not occ:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Occupation with ID '{occupation_id}' not found.",
            )
        return occ

    def compute_compatibility_for_resume(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CareerCompatibilityResponseSchema:
        """
        Computes career role compatibility across all occupations for a candidate's resume.
        Persists compatibility evaluation records to database.
        """
        resume = (
            self.db.query(Resume)
            .filter(Resume.id == resume_id, Resume.user_id == user_id)
            .first()
        )
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or access denied.",
            )

        occupations = self.get_all_occupations()
        if not occupations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No occupations found in taxonomy database.",
            )

        evaluations = self.engine.evaluate_role_compatibility(resume, occupations)

        # Persist evaluations idempotently
        role_schemas = []
        for eval_res in evaluations:
            occ_id = eval_res["occupation_id"]

            existing_compat = (
                self.db.query(CareerCompatibility)
                .filter(
                    CareerCompatibility.resume_id == resume_id,
                    CareerCompatibility.occupation_id == occ_id,
                )
                .first()
            )

            if existing_compat:
                existing_compat.compatibility_score = eval_res["compatibility_score"]
                existing_compat.summary_explanation = eval_res["summary_explanation"]
                # Clear old components
                existing_compat.components.clear()
                compat_record = existing_compat
            else:
                compat_record = CareerCompatibility(
                    user_id=user_id,
                    resume_id=resume_id,
                    occupation_id=occ_id,
                    compatibility_score=eval_res["compatibility_score"],
                    summary_explanation=eval_res["summary_explanation"],
                )
                self.db.add(compat_record)
                self.db.flush()

            component_schemas = []
            for comp in eval_res["components"]:
                c_obj = CareerCompatibilityComponent(
                    career_compatibility_id=compat_record.id,
                    component_name=comp["component_name"],
                    score=comp["score"],
                    weight=comp["weight"],
                    weighted_score=comp["weighted_score"],
                    explanation=comp["explanation"],
                )
                self.db.add(c_obj)
                component_schemas.append(CareerCompatibilityComponentSchema(**comp))

            role_schemas.append(
                CareerRoleMatchSchema(
                    occupation_id=occ_id,
                    occupation_title=eval_res["occupation_title"],
                    occupation_code=eval_res["occupation_code"],
                    category=eval_res["category"],
                    compatibility_score=eval_res["compatibility_score"],
                    summary_explanation=eval_res["summary_explanation"],
                    components=component_schemas,
                    strengths=eval_res["strengths"],
                    skill_gaps=eval_res["skill_gaps"],
                    matched_skills_count=eval_res["matched_skills_count"],
                    total_skills_count=eval_res["total_skills_count"],
                )
            )

        self.db.commit()

        return CareerCompatibilityResponseSchema(
            resume_id=resume_id,
            roles=role_schemas,
            matching_engine_version="1.0.0",
            scoring_version="1.0.0-heuristic",
        )
