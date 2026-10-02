"""Skill extraction for job descriptions reusing canonical Phase 3 taxonomy & alias infrastructure."""

import logging
from typing import Dict, List, Any, Optional
from uuid import UUID

from app.ai.extraction.skill_extractor import SkillExtractor
from app.ai.jobs.requirement_extractor import determine_priority

logger = logging.getLogger(__name__)


class JobSkillExtractor:
    """
    Extracts canonical technical skills from job description sections,
    determining requirement_type (REQUIRED / PREFERRED / UNKNOWN) based on
    explicit linguistic cues and section context, and preserving evidence sentences.
    """

    def __init__(self, base_extractor: Optional[SkillExtractor] = None):
        self.extractor = base_extractor or SkillExtractor()

    def extract_from_job_sections(
        self,
        sections: List[Dict[str, Any]],
        canonical_id_map: Dict[str, UUID],
    ) -> List[Dict[str, Any]]:
        """
        Extracts canonical skills from structured job sections.
        
        Args:
            sections: List of section dicts (section_type, section_title, content_text)
            canonical_id_map: Mapping of canonical skill name -> Skill UUID in database.
            
        Returns:
            List of job skill records with requirement_type and evidence.
        """
        job_skills: Dict[str, Dict[str, Any]] = {}

        for sec in sections:
            sec_type = sec["section_type"]
            sec_title = sec["section_title"]
            content = sec["content_text"]

            # Split into candidate sentences
            sentences = self.extractor._split_into_sentences(content)

            for sentence in sentences:
                candidate_matches = self.extractor._extract_skills_from_sentence(sentence)

                for match_text in candidate_matches:
                    normalized = self.extractor.alias_mapper.normalize(match_text)
                    if not normalized:
                        continue

                    canon_name = normalized.canonical_name
                    skill_id = canonical_id_map.get(canon_name)
                    if not skill_id:
                        continue

                    # Determine REQUIRED vs PREFERRED from sentence + section
                    priority, priority_evidence = determine_priority(sentence, sec_type)
                    confidence = round(normalized.confidence * (1.0 if priority != "UNKNOWN" else 0.90), 3)

                    # Evidence is the sentence where the skill was mentioned
                    evidence_text = sentence.strip()

                    # Priority rank: REQUIRED (2) > PREFERRED (1) > UNKNOWN (0)
                    priority_rank = {"REQUIRED": 2, "PREFERRED": 1, "UNKNOWN": 0}

                    # Deduplication / merge: elevate to higher priority if found in a more specific context
                    if canon_name in job_skills:
                        existing = job_skills[canon_name]
                        curr_rank = priority_rank.get(existing["requirement_type"], 0)
                        new_rank = priority_rank.get(priority, 0)
                        if new_rank > curr_rank:
                            existing["requirement_type"] = priority
                            existing["evidence_text"] = evidence_text
                            existing["source_section"] = sec_title
                            existing["confidence"] = max(existing["confidence"], confidence)
                    else:
                        job_skills[canon_name] = {
                            "skill_id": skill_id,
                            "raw_skill_text": match_text,
                            "canonical_skill_name": canon_name,
                            "requirement_type": priority,
                            "source_section": sec_title,
                            "evidence_text": evidence_text,
                            "confidence": confidence,
                            "taxonomy_sources": normalized.taxonomy_sources,
                        }

        return list(job_skills.values())
