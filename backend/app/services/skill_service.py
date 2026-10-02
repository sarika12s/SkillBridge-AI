"""Skill service orchestrating extraction, normalization, persistence, and querying."""

import logging
from typing import Dict, List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.resume import Resume, ResumeSection
from app.models.skill import Skill, SkillAlias, SkillRelationship, ResumeSkill
from app.schemas.skill import (
    SkillSchema,
    SkillAliasSchema,
    SkillRelationshipSchema,
    ExtractedSkillMatch,
    ResumeSkillsResponse,
)
from app.ai.extraction.skill_extractor import SkillExtractor
from app.data.seeders.seed_taxonomies import seed_taxonomies

logger = logging.getLogger(__name__)


class SkillService:
    def __init__(self, extractor: Optional[SkillExtractor] = None):
        self.extractor = extractor or SkillExtractor()

    def _ensure_taxonomy_seeded(self, db: Session) -> None:
        """Ensures canonical skills and aliases are in DB, seeding them if table is empty."""
        skill_count = db.query(Skill).count()
        if skill_count == 0:
            logger.info("No skills found in database. Running initial taxonomy seed...")
            seed_taxonomies(db, generate_embeddings=True)

    def extract_and_persist_resume_skills(
        self, resume_id: UUID, db: Session
    ) -> ResumeSkillsResponse:
        """
        Extracts skills from parsed resume sections, resolves canonical mappings,
        and persists ResumeSkill rows.
        """
        self._ensure_taxonomy_seeded(db)

        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID '{resume_id}' not found.",
            )

        # Collect text by section
        sections = db.query(ResumeSection).filter(ResumeSection.resume_id == resume_id).all()
        sections_dict: Dict[str, str] = {}
        if sections:
            for sec in sections:
                sections_dict[sec.section_type] = sec.content_text
        elif resume.raw_text:
            sections_dict["RESUME_BODY"] = resume.raw_text

        # Build canonical skill mapping: canonical_name -> Skill ID
        skills_in_db = db.query(Skill).all()
        canonical_id_map: Dict[str, UUID] = {s.name: s.id for s in skills_in_db}
        canonical_obj_map: Dict[str, Skill] = {s.name: s for s in skills_in_db}

        # Run extraction
        raw_matches = self.extractor.extract_from_sections(sections_dict, canonical_id_map)

        # Clear existing skill mentions for this resume (idempotent re-run)
        db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume_id).delete()
        db.flush()

        results: List[ExtractedSkillMatch] = []

        for item in raw_matches:
            canon_name = item["canonical_name"]
            db_skill = canonical_obj_map.get(canon_name)
            if not db_skill:
                continue

            resume_skill = ResumeSkill(
                resume_id=resume.id,
                skill_id=db_skill.id,
                raw_skill_text=item["original_text"],
                canonical_skill_name=canon_name,
                source_section=item["source_section"],
                evidence_sentence=item["evidence_sentence"],
                confidence=item["confidence"],
                match_method=item["normalization_method"],
            )
            db.add(resume_skill)

            results.append(
                ExtractedSkillMatch(
                    canonical_skill_id=db_skill.id,
                    canonical_name=canon_name,
                    original_text=item["original_text"],
                    source_section=item["source_section"],
                    evidence_sentence=item["evidence_sentence"],
                    normalization_method=item["normalization_method"],
                    taxonomy_sources=[db_skill.taxonomy_source],
                    embedding_available=db_skill.embedding is not None,
                    confidence=item["confidence"],
                )
            )

        db.commit()

        return ResumeSkillsResponse(
            resume_id=resume.id,
            total_skills_extracted=len(results),
            skills=results,
        )

    def get_resume_skills(self, resume_id: UUID, db: Session) -> ResumeSkillsResponse:
        """
        Retrieves extracted skills for a resume.
        Auto-extracts if not yet extracted.
        """
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID '{resume_id}' not found.",
            )

        existing_skills = (
            db.query(ResumeSkill)
            .filter(ResumeSkill.resume_id == resume_id)
            .order_by(ResumeSkill.confidence.desc())
            .all()
        )

        if not existing_skills:
            # Auto-extract if sections exist
            return self.extract_and_persist_resume_skills(resume_id, db)

        matches: List[ExtractedSkillMatch] = []
        for r_skill in existing_skills:
            skill = r_skill.skill
            matches.append(
                ExtractedSkillMatch(
                    canonical_skill_id=r_skill.skill_id,
                    canonical_name=r_skill.canonical_skill_name,
                    original_text=r_skill.raw_skill_text,
                    source_section=r_skill.source_section,
                    evidence_sentence=r_skill.evidence_sentence,
                    normalization_method=r_skill.match_method,
                    taxonomy_sources=[skill.taxonomy_source] if skill else ["CUSTOM"],
                    embedding_available=skill.embedding is not None if skill else False,
                    confidence=r_skill.confidence,
                )
            )

        return ResumeSkillsResponse(
            resume_id=resume.id,
            total_skills_extracted=len(matches),
            skills=matches,
        )

    def get_skill_by_id(self, skill_id: UUID, db: Session) -> SkillSchema:
        """Retrieves canonical skill details including aliases and relationships."""
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with ID '{skill_id}' not found.",
            )

        aliases = [
            SkillAliasSchema(
                id=a.id,
                alias=a.alias,
                alias_type=a.alias_type,
                source=a.source,
                confidence=a.confidence,
            )
            for a in skill.aliases
        ]

        relationships = [
            SkillRelationshipSchema(
                id=rel.id,
                source_skill_id=rel.source_skill_id,
                target_skill_id=rel.target_skill_id,
                target_skill_name=rel.target_skill.name if rel.target_skill else None,
                relationship_type=rel.relationship_type,
                strength_weight=rel.strength_weight,
                source=rel.source,
                confidence=rel.confidence,
            )
            for rel in skill.source_relationships
        ]

        return SkillSchema(
            id=skill.id,
            name=skill.name,
            normalized_name=skill.normalized_name,
            category=skill.category,
            taxonomy_source=skill.taxonomy_source,
            taxonomy_code=skill.taxonomy_code,
            description=skill.description,
            embedding_available=skill.embedding is not None,
            aliases=aliases,
            relationships=relationships,
        )

    def get_skill_relationships(
        self, skill_id: UUID, db: Session
    ) -> List[SkillRelationshipSchema]:
        """Retrieves all ontology relationships where skill is source or target."""
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with ID '{skill_id}' not found.",
            )

        rels = (
            db.query(SkillRelationship)
            .filter(
                (SkillRelationship.source_skill_id == skill_id)
                | (SkillRelationship.target_skill_id == skill_id)
            )
            .all()
        )

        output: List[SkillRelationshipSchema] = []
        for r in rels:
            output.append(
                SkillRelationshipSchema(
                    id=r.id,
                    source_skill_id=r.source_skill_id,
                    target_skill_id=r.target_skill_id,
                    target_skill_name=r.target_skill.name if r.target_skill else None,
                    relationship_type=r.relationship_type,
                    strength_weight=r.strength_weight,
                    source=r.source,
                    confidence=r.confidence,
                )
            )

        return output
