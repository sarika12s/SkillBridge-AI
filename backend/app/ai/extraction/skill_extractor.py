"""Skill candidate extraction engine preserving section source, evidence sentence, and taxonomy mapping."""

import logging
import re
from typing import Dict, List, Any, Optional, Set
from uuid import UUID

from app.ai.normalization.alias_mapper import AliasMapper, NormalizedSkillResult

logger = logging.getLogger(__name__)


class SkillExtractor:
    """
    NLP & Lexicon-based skill candidate extractor.
    Extracts multi-word phrases and single-word tokens from structured resume sections,
    extracts the evidence sentence, and resolves them via AliasMapper.
    """

    def __init__(self, alias_mapper: Optional[AliasMapper] = None):
        self.alias_mapper = alias_mapper or AliasMapper()
        self._build_search_vocab()

    def _build_search_vocab(self) -> None:
        """
        Builds a sorted vocabulary of all canonical skills and aliases (longest first)
        for greedy multi-word phrase matching.
        """
        vocab = set()
        for name in self.alias_mapper.canonical_skills.keys():
            vocab.add(name)
        for alias_norm, meta in self.alias_mapper.aliases.items():
            vocab.add(alias_norm)

        # Sort by length descending so multi-word phrases (e.g. "React Native", "Machine Learning")
        # are matched before subsets (e.g. "React")
        self._sorted_terms = sorted(list(vocab), key=lambda x: len(x), reverse=True)

    def extract_from_sections(
        self,
        sections: Dict[str, str],
        canonical_id_map: Optional[Dict[str, UUID]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extracts skills from parsed resume sections.
        
        Args:
            sections: Dictionary of section_name -> section_content_text
            canonical_id_map: Optional mapping of canonical skill name to DB UUID
            
        Returns:
            List of extracted skill dictionaries with evidence and metadata.
        """
        canonical_id_map = canonical_id_map or {}
        extracted_skills: Dict[str, Dict[str, Any]] = {}

        # Prioritize dedicated skill sections first, followed by experience, projects, etc.
        section_weights = {
            "SKILLS": 1.0,
            "TECHNICAL_SKILLS": 1.0,
            "TOOLS": 1.0,
            "PROJECTS": 0.95,
            "EXPERIENCE": 0.95,
            "WORK_EXPERIENCE": 0.95,
            "CERTIFICATIONS": 0.90,
            "EDUCATION": 0.85,
            "OTHER": 0.80,
        }

        for sec_name, content in sections.items():
            if not content or not content.strip():
                continue

            sec_upper = sec_name.strip().upper()
            sec_weight = section_weights.get(sec_upper, 0.80)

            # Split section text into candidate sentences / bullet lines
            sentences = self._split_into_sentences(content)

            for sentence in sentences:
                found_in_sentence = self._extract_skills_from_sentence(sentence)
                for match_text in found_in_sentence:
                    normalized = self.alias_mapper.normalize(match_text)
                    if not normalized:
                        continue

                    canon_name = normalized.canonical_name
                    confidence = round(normalized.confidence * sec_weight, 3)

                    # If already extracted, only update if higher confidence or richer evidence
                    if canon_name in extracted_skills:
                        existing = extracted_skills[canon_name]
                        if confidence > existing["confidence"]:
                            existing["original_text"] = match_text
                            existing["source_section"] = sec_upper
                            existing["evidence_sentence"] = sentence
                            existing["confidence"] = confidence
                            existing["normalization_method"] = normalized.method
                    else:
                        skill_id = canonical_id_map.get(canon_name)
                        extracted_skills[canon_name] = {
                            "canonical_skill_id": skill_id,
                            "canonical_name": canon_name,
                            "original_text": match_text,
                            "source_section": sec_upper,
                            "evidence_sentence": sentence,
                            "normalization_method": normalized.method,
                            "confidence": confidence,
                            "category": normalized.category,
                            "taxonomy_sources": normalized.taxonomy_sources,
                            "embedding_available": True,
                        }

        return list(extracted_skills.values())

    def _split_into_sentences(self, text: str) -> List[str]:
        """Splits section text into sentences, bullet points, and clean lines."""
        lines = re.split(r"[\r\n]+|[•\*\-\–\—]\s+|;\s+", text)
        sentences = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            # Further split by periods followed by space and capital letter if long
            sub_sentences = re.split(r"\.\s+(?=[A-Z])", line_str)
            for sub in sub_sentences:
                clean_sub = sub.strip()
                if len(clean_sub) >= 2:
                    sentences.append(clean_sub)
        return sentences

    def _extract_skills_from_sentence(self, sentence: str) -> Set[str]:
        """
        Detects skill candidate mentions within a single sentence.
        Uses boundary-aware regex matching to extract exact token mentions.
        """
        found_matches: Set[str] = set()
        matched_spans: List[tuple] = []

        # Iterate through terms sorted by length descending
        for term in self._sorted_terms:
            # Build regex with word boundaries where appropriate
            escaped_term = re.escape(term)
            
            # If term contains non-alphanumeric at boundaries (e.g. C++, CI/CD, .NET)
            pattern_str = rf"(?<![\w#+]){escaped_term}(?![\w#+])"
            pattern = re.compile(pattern_str, re.IGNORECASE)

            for match in pattern.finditer(sentence):
                start, end = match.span()
                # Ensure no overlapping span from longer match
                overlap = any(
                    (start >= s_start and start < s_end) or (end > s_start and end <= s_end)
                    for s_start, s_end in matched_spans
                )
                if not overlap:
                    matched_spans.append((start, end))
                    found_matches.add(match.group())

        return found_matches
