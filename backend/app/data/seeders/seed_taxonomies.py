"""Seeder script to load ESCO, O*NET, curated aliases, and relationships into database."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.skill import Skill, SkillAlias, SkillRelationship
from app.ai.matching.vector_embedder import VectorEmbedder

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent


def seed_taxonomies(db: Session, generate_embeddings: bool = True) -> Dict[str, Any]:
    """
    Idempotently seeds ESCO and O*NET taxonomies, aliases, and relationships.
    Generates 384-dimensional dense vectors using VectorEmbedder.
    """
    esco_file = DATA_DIR / "taxonomies" / "esco_skills.json"
    onet_file = DATA_DIR / "taxonomies" / "onet_skills.json"
    aliases_file = DATA_DIR / "aliases" / "skill_aliases.json"
    relationships_file = DATA_DIR / "taxonomies" / "skill_relationships.json"

    embedder = VectorEmbedder() if generate_embeddings else None

    # 1. Load canonical skills from ESCO and O*NET
    canonical_skills = []
    if esco_file.exists():
        with open(esco_file, "r", encoding="utf-8") as f:
            canonical_skills.extend(json.load(f))
    if onet_file.exists():
        with open(onet_file, "r", encoding="utf-8") as f:
            canonical_skills.extend(json.load(f))

    skill_name_to_id: Dict[str, Any] = {}
    skills_seeded = 0
    embeddings_count = 0

    for item in canonical_skills:
        name = item["name"].strip()
        norm_name = name.lower()
        existing = db.query(Skill).filter(Skill.name == name).first()

        embedding_vector = None
        if generate_embeddings and embedder:
            embed_text = f"{name}: {item.get('description', '')}"
            embedding_vector = embedder.generate_embedding(embed_text)
            embeddings_count += 1

        if not existing:
            skill = Skill(
                name=name,
                normalized_name=norm_name,
                category=item.get("category", "TECHNICAL_SKILL"),
                taxonomy_source=item.get("taxonomy_source", "CUSTOM"),
                taxonomy_code=item.get("taxonomy_code"),
                description=item.get("description"),
                embedding=embedding_vector,
            )
            db.add(skill)
            db.flush()
            skill_name_to_id[name] = skill.id
            skills_seeded += 1
        else:
            # Update fields if changed
            existing.category = item.get("category", existing.category)
            existing.taxonomy_source = item.get("taxonomy_source", existing.taxonomy_source)
            existing.taxonomy_code = item.get("taxonomy_code", existing.taxonomy_code)
            existing.description = item.get("description", existing.description)
            if embedding_vector is not None:
                existing.embedding = embedding_vector
            db.flush()
            skill_name_to_id[name] = existing.id

    # 2. Load and seed aliases
    aliases_seeded = 0
    if aliases_file.exists():
        with open(aliases_file, "r", encoding="utf-8") as f:
            alias_list = json.load(f)

        for alias_entry in alias_list:
            canonical_name = alias_entry.get("canonical_skill")
            skill_id = skill_name_to_id.get(canonical_name)
            if not skill_id:
                # Skill could be in DB from earlier run
                found_skill = db.query(Skill).filter(Skill.name == canonical_name).first()
                if found_skill:
                    skill_id = found_skill.id
                    skill_name_to_id[canonical_name] = skill_id

            if not skill_id:
                logger.warning(f"Canonical skill '{canonical_name}' not found for alias '{alias_entry.get('alias')}'")
                continue

            raw_alias = alias_entry.get("alias", "").strip()
            norm_alias = raw_alias.lower()

            existing_alias = (
                db.query(SkillAlias)
                .filter(SkillAlias.skill_id == skill_id, SkillAlias.alias == raw_alias)
                .first()
            )
            if not existing_alias:
                alias_obj = SkillAlias(
                    skill_id=skill_id,
                    alias=raw_alias,
                    normalized_alias=norm_alias,
                    alias_type=alias_entry.get("alias_type", "SYNONYM"),
                    source=alias_entry.get("source", "CURATED_TECH_DICT"),
                    confidence=alias_entry.get("confidence", 1.0),
                )
                db.add(alias_obj)
                aliases_seeded += 1

    # 3. Load and seed relationships
    relationships_seeded = 0
    if relationships_file.exists():
        with open(relationships_file, "r", encoding="utf-8") as f:
            rel_list = json.load(f)

        for rel in rel_list:
            src_name = rel.get("source_skill")
            tgt_name = rel.get("target_skill")

            src_id = skill_name_to_id.get(src_name) or getattr(
                db.query(Skill).filter(Skill.name == src_name).first(), "id", None
            )
            tgt_id = skill_name_to_id.get(tgt_name) or getattr(
                db.query(Skill).filter(Skill.name == tgt_name).first(), "id", None
            )

            if not src_id or not tgt_id:
                logger.warning(f"Could not link relationship between '{src_name}' and '{tgt_name}'")
                continue

            rel_type = rel.get("relationship_type")
            existing_rel = (
                db.query(SkillRelationship)
                .filter(
                    SkillRelationship.source_skill_id == src_id,
                    SkillRelationship.target_skill_id == tgt_id,
                    SkillRelationship.relationship_type == rel_type,
                )
                .first()
            )
            if not existing_rel:
                rel_obj = SkillRelationship(
                    source_skill_id=src_id,
                    target_skill_id=tgt_id,
                    relationship_type=rel_type,
                    strength_weight=rel.get("strength_weight", 1.0),
                    confidence=rel.get("confidence", 1.0),
                    source=rel.get("source", "CURATED_KNOWLEDGE_GRAPH"),
                )
                db.add(rel_obj)
                relationships_seeded += 1

    db.commit()

    # 4. Seed Occupations and OccupationSkills
    occupations_seeded = seed_occupations(db)

    # 5. Seed Curated Learning Resources
    resources_seeded = seed_learning_resources(db)

    summary = {
        "skills_seeded": skills_seeded,
        "aliases_seeded": aliases_seeded,
        "relationships_seeded": relationships_seeded,
        "occupations_seeded": occupations_seeded,
        "resources_seeded": resources_seeded,
        "embeddings_generated": embeddings_count,
        "total_canonical_skills": db.query(Skill).count(),
        "total_aliases": db.query(SkillAlias).count(),
        "total_relationships": db.query(SkillRelationship).count(),
    }
    logger.info(f"Taxonomy seeding summary: {summary}")
    return summary


def seed_occupations(db: Session) -> int:
    """Idempotently seeds standardized occupations and requirements from occupations.json."""
    from app.models.career import Occupation, OccupationSkill

    occupations_file = DATA_DIR / "occupations" / "occupations.json"
    if not occupations_file.exists():
        return 0

    with open(occupations_file, "r", encoding="utf-8") as f:
        occupations_data = json.load(f)

    seeded_count = 0
    for item in occupations_data:
        code = item["code"]
        existing = db.query(Occupation).filter(Occupation.code == code).first()
        if not existing:
            occ = Occupation(
                code=code,
                title=item["title"],
                normalized_title=item["title"].lower(),
                description=item["description"],
                category=item.get("category", "SOFTWARE_DEVELOPMENT"),
                source=item.get("source", "ESCO"),
                source_version=item.get("source_version", "v1.2"),
            )
            db.add(occ)
            db.flush()
            existing = occ
            seeded_count += 1

        # Link skills
        for sk_info in item.get("skills", []):
            sk_name = sk_info["skill_name"]
            skill = db.query(Skill).filter(Skill.name == sk_name).first()
            if not skill:
                skill = db.query(Skill).filter(Skill.normalized_name == sk_name.lower()).first()
            if skill:
                occ_sk = (
                    db.query(OccupationSkill)
                    .filter(
                        OccupationSkill.occupation_id == existing.id,
                        OccupationSkill.skill_id == skill.id,
                    )
                    .first()
                )
                if not occ_sk:
                    occ_sk = OccupationSkill(
                        occupation_id=existing.id,
                        skill_id=skill.id,
                        requirement_type=sk_info.get("requirement_type", "REQUIRED"),
                        importance_weight=sk_info.get("importance_weight", 1.0),
                    )
                    db.add(occ_sk)

    db.commit()
    return seeded_count


def seed_learning_resources(db: Session) -> int:
    """Idempotently seeds curated, genuine learning resources from learning_resources.json."""
    from app.models.learning import LearningResource

    resources_file = DATA_DIR / "resources" / "learning_resources.json"
    if not resources_file.exists():
        return 0

    with open(resources_file, "r", encoding="utf-8") as f:
        resources_data = json.load(f)

    seeded_count = 0
    for item in resources_data:
        sk_name = item["skill_name"]
        skill = db.query(Skill).filter(Skill.name == sk_name).first()
        if not skill:
            skill = db.query(Skill).filter(Skill.normalized_name == sk_name.lower()).first()
        if not skill:
            continue

        existing = (
            db.query(LearningResource)
            .filter(
                LearningResource.skill_id == skill.id,
                LearningResource.url == item["url"],
            )
            .first()
        )
        if not existing:
            res = LearningResource(
                skill_id=skill.id,
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
            db.add(res)
            seeded_count += 1

    db.commit()
    return seeded_count


if __name__ == "__main__":
    db = SessionLocal()
    try:
        res = seed_taxonomies(db, generate_embeddings=True)
        print("Taxonomy Seeding Succeeded:", res)
    finally:
        db.close()

