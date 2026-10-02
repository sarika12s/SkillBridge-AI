"""Hybrid Matching Engine combining Exact Canonical, Alias, Taxonomy, and Semantic Signals."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from app.ai.matching.config import matching_config
from app.ai.matching.vector_embedder import VectorEmbedder, embedder
from app.models.skill import Skill, SkillRelationship, ResumeSkill
from app.models.job import JobSkill

logger = logging.getLogger(__name__)


class SkillMatchingEngine:
    """
    Hybrid Skill Matching Engine that preserves distinct inspectable signals:
    - EXACT_MATCH (Exact canonical ID)
    - ALIAS_MATCH (Phase 3 alias mapping)
    - TAXONOMY_MATCH (EQUIVALENT vs RELATED_SUPPORT)
    - SEMANTIC_MATCH (Cosine vector similarity with strict thresholds)
    - EVIDENCE_SIGNAL (Traceable sentence justification)
    """

    def __init__(self, vector_embedder: Optional[VectorEmbedder] = None):
        self.embedder = vector_embedder or embedder

    def match_job_skill_to_resume_skills(
        self,
        job_skill: JobSkill,
        resume_skills: List[ResumeSkill],
        canonical_skills_map: Dict[UUID, Skill],
        relationships: List[SkillRelationship],
    ) -> Dict[str, Any]:
        """
        Evaluates a single JobSkill against all candidate ResumeSkills.
        Returns the best deterministic match result with full signal breakdown.
        """
        job_canon_id = job_skill.skill_id
        job_canon_name = job_skill.canonical_skill_name
        job_priority = job_skill.requirement_type or "REQUIRED"
        job_evidence = job_skill.evidence_text

        best_match: Optional[Dict[str, Any]] = None

        # 1. First Pass: Check for Exact Canonical Match (Highest Precedence)
        for r_skill in resume_skills:
            if r_skill.skill_id == job_canon_id:
                status = "MATCHED_REQUIRED" if job_priority == "REQUIRED" else "MATCHED_PREFERRED"
                return {
                    "job_skill_id": job_skill.id,
                    "resume_skill_id": r_skill.id,
                    "canonical_skill_id": job_canon_id,
                    "canonical_skill_name": job_canon_name,
                    "match_type": "DIRECT_MATCH",
                    "match_status": status,
                    "priority": job_priority,
                    "confidence": 1.0,
                    "similarity_score": 1.0,
                    "resume_evidence": r_skill.evidence_sentence,
                    "job_evidence": job_evidence,
                    "explanation": (
                        f"Exact canonical match verified: Candidate demonstrated '{r_skill.canonical_skill_name}' "
                        f"in '{r_skill.source_section}' matching job requirement."
                    ),
                }

        # 2. Second Pass: Check Alias Match
        for r_skill in resume_skills:
            if r_skill.canonical_skill_name.strip().lower() == job_canon_name.strip().lower():
                status = "MATCHED_REQUIRED" if job_priority == "REQUIRED" else "MATCHED_PREFERRED"
                return {
                    "job_skill_id": job_skill.id,
                    "resume_skill_id": r_skill.id,
                    "canonical_skill_id": job_canon_id or r_skill.skill_id,
                    "canonical_skill_name": job_canon_name,
                    "match_type": "ALIAS_MATCH",
                    "match_status": status,
                    "priority": job_priority,
                    "confidence": 0.98,
                    "similarity_score": 0.99,
                    "resume_evidence": r_skill.evidence_sentence,
                    "job_evidence": job_evidence,
                    "explanation": (
                        f"Alias match: Candidate's '{r_skill.raw_skill_text}' resolved to "
                        f"canonical '{job_canon_name}', matching job requirement."
                    ),
                }

        # 3. Third Pass: Check Explicit Taxonomy Relationships (ESCO / O*NET)
        for rel in relationships:
            # Check if this relationship links job_canon_id and any candidate resume_skill.skill_id
            for r_skill in resume_skills:
                is_forward = (rel.source_skill_id == r_skill.skill_id and rel.target_skill_id == job_canon_id)
                is_reverse = (rel.target_skill_id == r_skill.skill_id and rel.source_skill_id == job_canon_id)

                if is_forward or is_reverse:
                    rel_type = rel.relationship_type.upper()
                    if rel_type in ("EQUIVALENT", "SYNONYM", "SAME_AS"):
                        status = "MATCHED_REQUIRED" if job_priority == "REQUIRED" else "MATCHED_PREFERRED"
                        return {
                            "job_skill_id": job_skill.id,
                            "resume_skill_id": r_skill.id,
                            "canonical_skill_id": job_canon_id,
                            "canonical_skill_name": job_canon_name,
                            "match_type": "TAXONOMY_EQUIVALENT",
                            "match_status": status,
                            "priority": job_priority,
                            "confidence": round(rel.confidence * 0.95, 3),
                            "similarity_score": 0.95,
                            "resume_evidence": r_skill.evidence_sentence,
                            "job_evidence": job_evidence,
                            "explanation": (
                                f"Taxonomy equivalence: '{r_skill.canonical_skill_name}' is formally mapped "
                                f"as equivalent to '{job_canon_name}' in ESCO/O*NET taxonomy."
                            ),
                        }
                    elif rel_type in ("RELATED_TO", "SUBSKILL_OF", "PART_OF", "PREREQUISITE_OF", "USED_WITH"):
                        # Related skills provide supporting evidence, but do NOT satisfy required skills automatically!
                        if best_match is None or best_match.get("confidence", 0) < 0.70:
                            best_match = {
                                "job_skill_id": job_skill.id,
                                "resume_skill_id": r_skill.id,
                                "canonical_skill_id": job_canon_id,
                                "canonical_skill_name": job_canon_name,
                                "match_type": "RELATED_SUPPORT",
                                "match_status": "RELATED_SUPPORT",
                                "priority": job_priority,
                                "confidence": round(rel.confidence * 0.70, 3),
                                "similarity_score": 0.75,
                                "resume_evidence": r_skill.evidence_sentence,
                                "job_evidence": job_evidence,
                                "explanation": (
                                    f"Supporting relationship detected: '{r_skill.canonical_skill_name}' is a "
                                    f"{rel_type.lower().replace('_', ' ')} of '{job_canon_name}'. "
                                    f"Contributes supporting evidence but does not automatically fulfill requirement."
                                ),
                            }

        # 4. Fourth Pass: Dense Semantic Vector Matching with False-Positive Guards
        job_skill_obj = canonical_skills_map.get(job_canon_id)
        job_embedding = job_skill_obj.embedding if job_skill_obj and job_skill_obj.embedding is not None else None

        if job_embedding is None and self.embedder.is_available:
            job_embedding = self.embedder.generate_embedding(job_canon_name)

        if job_embedding is not None:
            for r_skill in resume_skills:
                # Check False-Positive Guard
                if self._is_strictly_prohibited_pair(r_skill.canonical_skill_name, job_canon_name):
                    continue

                r_skill_obj = canonical_skills_map.get(r_skill.skill_id)
                r_embedding = r_skill_obj.embedding if r_skill_obj and r_skill_obj.embedding is not None else None
                if r_embedding is None and self.embedder.is_available:
                    r_embedding = self.embedder.generate_embedding(r_skill.canonical_skill_name)

                if r_embedding is not None:
                    similarity = self.embedder.compute_cosine_similarity(r_embedding, job_embedding)

                    if similarity >= matching_config.HIGH_SEMANTIC_THRESHOLD:
                        # Strong semantic match (>= 0.82)
                        status = "MATCHED_REQUIRED" if job_priority == "REQUIRED" else "MATCHED_PREFERRED"
                        sim_match = {
                            "job_skill_id": job_skill.id,
                            "resume_skill_id": r_skill.id,
                            "canonical_skill_id": job_canon_id,
                            "canonical_skill_name": job_canon_name,
                            "match_type": "SEMANTIC_MATCH",
                            "match_status": status,
                            "priority": job_priority,
                            "confidence": round(float(similarity), 3),
                            "similarity_score": round(float(similarity), 3),
                            "resume_evidence": r_skill.evidence_sentence,
                            "job_evidence": job_evidence,
                            "explanation": (
                                f"High semantic similarity ({similarity:.2f} >= {matching_config.HIGH_SEMANTIC_THRESHOLD}): "
                                f"'{r_skill.canonical_skill_name}' strongly aligns contextually with '{job_canon_name}'."
                            ),
                        }
                        if best_match is None or sim_match["confidence"] > best_match["confidence"]:
                            best_match = sim_match

                    elif similarity >= matching_config.MEDIUM_SEMANTIC_THRESHOLD:
                        # Moderate semantic similarity (0.70 <= sim < 0.82) -> PARTIAL_MATCH
                        status = "PARTIAL_REQUIRED" if job_priority == "REQUIRED" else "PARTIAL_PREFERRED"
                        partial_match = {
                            "job_skill_id": job_skill.id,
                            "resume_skill_id": r_skill.id,
                            "canonical_skill_id": job_canon_id,
                            "canonical_skill_name": job_canon_name,
                            "match_type": "PARTIAL_MATCH",
                            "match_status": status,
                            "priority": job_priority,
                            "confidence": round(float(similarity) * 0.80, 3),
                            "similarity_score": round(float(similarity), 3),
                            "resume_evidence": r_skill.evidence_sentence,
                            "job_evidence": job_evidence,
                            "explanation": (
                                f"Moderate semantic proximity ({similarity:.2f}): '{r_skill.canonical_skill_name}' "
                                f"partially relates to '{job_canon_name}', representing a partial conceptual overlap."
                            ),
                        }
                        if best_match is None or (best_match["match_type"] not in ("SEMANTIC_MATCH", "RELATED_SUPPORT") and partial_match["confidence"] > best_match["confidence"]):
                            best_match = partial_match

        # 5. Fallback: If no match found, classify as MISSING
        if best_match is None:
            status = "MISSING_REQUIRED" if job_priority == "REQUIRED" else "MISSING_PREFERRED"
            return {
                "job_skill_id": job_skill.id,
                "resume_skill_id": None,
                "canonical_skill_id": job_canon_id,
                "canonical_skill_name": job_canon_name,
                "match_type": "NO_MATCH",
                "match_status": status,
                "priority": job_priority,
                "confidence": 0.0,
                "similarity_score": 0.0,
                "resume_evidence": None,
                "job_evidence": job_evidence,
                "explanation": (
                    f"Requirement unfulfilled: '{job_canon_name}' is {job_priority.lower()} for this role, "
                    f"but no equivalent, alias, or sufficiently similar skill was detected on the resume."
                ),
            }

        return best_match

    def _is_strictly_prohibited_pair(self, name_a: str, name_b: str) -> bool:
        """
        Enforces critical domain distinction guards.
        Prevents false positives like Java vs JavaScript, React vs React Native,
        AWS vs Azure, and SQL vs PostgreSQL.
        """
        a = name_a.strip().lower()
        b = name_b.strip().lower()

        if a == b:
            return False

        for pair_a, pair_b in matching_config.STRICT_DISTINCT_PAIRS:
            if (a == pair_a and b == pair_b) or (a == pair_b and b == pair_a):
                return True

        return False
