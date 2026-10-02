"""Skill Normalization and Alias Resolution Engine with distinction enforcement."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# Conflicting technology pairs that must NEVER be conflated
DISTINCT_TECH_PAIRS = [
    ("java", "javascript"),
    ("c", "c++"),
    ("c", "c#"),
    ("react", "react native"),
    ("amazon web services", "microsoft azure"),
    ("aws", "azure"),
    ("sql", "mysql"),
    ("sql", "postgresql"),
    ("tensorflow", "pytorch"),
]


class NormalizedSkillResult:
    def __init__(
        self,
        original_text: str,
        canonical_name: str,
        canonical_id: Optional[str],
        method: str,
        confidence: float,
        category: str,
        taxonomy_sources: List[str],
    ):
        self.original_text = original_text
        self.canonical_name = canonical_name
        self.canonical_id = canonical_id
        self.method = method  # 'EXACT', 'ALIAS', 'SPELLING_VARIANT', 'SYNONYM', 'ACRONYM'
        self.confidence = confidence
        self.category = category
        self.taxonomy_sources = taxonomy_sources

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "canonical_name": self.canonical_name,
            "canonical_id": str(self.canonical_id) if self.canonical_id else None,
            "method": self.method,
            "confidence": self.confidence,
            "category": self.category,
            "taxonomy_sources": self.taxonomy_sources,
        }


class AliasMapper:
    """
    Curated skill normalization engine.
    Resolves variations (e.g., JS -> JavaScript, Postgres -> PostgreSQL, ReactJS -> React)
    while enforcing distinction rules (e.g. Java != JavaScript, C != C++).
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR
        self._canonical_skills: Dict[str, Dict[str, Any]] = {}
        self._normalized_to_canonical: Dict[str, str] = {}
        self._alias_lookup: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
        self.load_data()

    def load_data(self) -> None:
        """Loads canonical skills and aliases from local datasets."""
        esco_file = self.data_dir / "taxonomies" / "esco_skills.json"
        onet_file = self.data_dir / "taxonomies" / "onet_skills.json"
        aliases_file = self.data_dir / "aliases" / "skill_aliases.json"

        # Load canonical ESCO skills
        if esco_file.exists():
            with open(esco_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    name = item["name"]
                    norm = self._clean_token(name)
                    self._canonical_skills[name] = {
                        "name": name,
                        "category": item.get("category", "TECHNICAL_SKILL"),
                        "taxonomy_sources": ["ESCO"],
                        "code": item.get("taxonomy_code"),
                        "description": item.get("description"),
                    }
                    self._normalized_to_canonical[norm] = name

        # Load canonical O*NET skills
        if onet_file.exists():
            with open(onet_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    name = item["name"]
                    norm = self._clean_token(name)
                    if name in self._canonical_skills:
                        if "ONET" not in self._canonical_skills[name]["taxonomy_sources"]:
                            self._canonical_skills[name]["taxonomy_sources"].append("ONET")
                    else:
                        self._canonical_skills[name] = {
                            "name": name,
                            "category": item.get("category", "TECHNICAL_SKILL"),
                            "taxonomy_sources": ["ONET"],
                            "code": item.get("taxonomy_code"),
                            "description": item.get("description"),
                        }
                        self._normalized_to_canonical[norm] = name

        # Load curated aliases
        if aliases_file.exists():
            with open(aliases_file, "r", encoding="utf-8") as f:
                for alias_item in json.load(f):
                    alias_str = alias_item.get("alias", "")
                    canonical = alias_item.get("canonical_skill", "")
                    norm_alias = self._clean_token(alias_str)
                    if norm_alias and canonical in self._canonical_skills:
                        self._alias_lookup[norm_alias] = {
                            "canonical_skill": canonical,
                            "alias_type": alias_item.get("alias_type", "SYNONYM"),
                            "confidence": alias_item.get("confidence", 1.0),
                            "source": alias_item.get("source", "CURATED_TECH_DICT"),
                        }

        self._loaded = True
        logger.info(
            f"AliasMapper loaded {len(self._canonical_skills)} canonical skills and {len(self._alias_lookup)} aliases."
        )

    def _clean_token(self, text: str) -> str:
        """Lowercases and cleans trailing punctuation while preserving symbols like +, #, ."""
        if not text:
            return ""
        # Keep letters, numbers, +, #, ., / and hyphens
        cleaned = text.strip().lower()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    def normalize(self, raw_text: str) -> Optional[NormalizedSkillResult]:
        """
        Normalizes a candidate skill string to its canonical taxonomy representation.
        Enforces strict distinction guards to prevent false matches.
        """
        if not raw_text or not raw_text.strip():
            return None

        clean_raw = raw_text.strip()
        norm_key = self._clean_token(clean_raw)

        # 1. Exact canonical name match (case-insensitive)
        if norm_key in self._normalized_to_canonical:
            canonical_name = self._normalized_to_canonical[norm_key]
            skill_info = self._canonical_skills[canonical_name]
            method = "EXACT" if clean_raw.lower() == canonical_name.lower() else "SPELLING_VARIANT"
            return NormalizedSkillResult(
                original_text=clean_raw,
                canonical_name=canonical_name,
                canonical_id=None,
                method=method,
                confidence=1.0,
                category=skill_info["category"],
                taxonomy_sources=skill_info["taxonomy_sources"],
            )

        # 2. Curated Alias Lookup
        if norm_key in self._alias_lookup:
            alias_meta = self._alias_lookup[norm_key]
            canonical_name = alias_meta["canonical_skill"]
            skill_info = self._canonical_skills[canonical_name]

            # Verify distinction check
            if not self._passes_distinction_check(clean_raw, canonical_name):
                return None

            return NormalizedSkillResult(
                original_text=clean_raw,
                canonical_name=canonical_name,
                canonical_id=None,
                method=alias_meta["alias_type"],
                confidence=alias_meta["confidence"],
                category=skill_info["category"],
                taxonomy_sources=skill_info["taxonomy_sources"],
            )

        # 3. Punctuation stripped alias match (e.g., 'react-js' -> 'reactjs')
        stripped_key = re.sub(r"[\.\-_/\s]", "", norm_key)
        for alias_norm, alias_meta in self._alias_lookup.items():
            if re.sub(r"[\.\-_/\s]", "", alias_norm) == stripped_key:
                canonical_name = alias_meta["canonical_skill"]
                skill_info = self._canonical_skills[canonical_name]
                if self._passes_distinction_check(clean_raw, canonical_name):
                    return NormalizedSkillResult(
                        original_text=clean_raw,
                        canonical_name=canonical_name,
                        canonical_id=None,
                        method="SPELLING_VARIANT",
                        confidence=alias_meta["confidence"] * 0.98,
                        category=skill_info["category"],
                        taxonomy_sources=skill_info["taxonomy_sources"],
                    )

        return None

    def _passes_distinction_check(self, candidate: str, canonical: str) -> bool:
        """
        Enforces that distinct technologies are not falsely conflated.
        e.g., candidate "Java" must not normalize to "JavaScript",
        candidate "C" must not normalize to "C++".
        """
        cand_lower = candidate.strip().lower()
        canon_lower = canonical.strip().lower()

        for term_a, term_b in DISTINCT_TECH_PAIRS:
            if cand_lower == term_a and canon_lower == term_b:
                return False
            if cand_lower == term_b and canon_lower == term_a:
                return False

        return True

    @property
    def canonical_skills(self) -> Dict[str, Dict[str, Any]]:
        return self._canonical_skills

    @property
    def aliases(self) -> Dict[str, Dict[str, Any]]:
        return self._alias_lookup
