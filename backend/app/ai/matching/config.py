"""Centralized configuration for matching thresholds and scoring weights in SkillBridge AI."""

from typing import Dict, Any


class MatchingConfig:
    """
    Centralized, versioned configuration for matching engine thresholds and scoring weights.
    All weights are explicitly labeled as INITIAL_HEURISTIC_WEIGHTS for academic transparency
    and are calibrated to sum to 1.00.
    """

    MATCHING_ENGINE_VERSION: str = "1.0.0"
    SCORING_VERSION: str = "1.0.0-heuristic"
    TAXONOMY_VERSIONS: str = "ESCO-v1.2,ONET-v28.0"

    # Semantic similarity thresholds for sentence-transformers/all-MiniLM-L6-v2:
    # - HIGH (>= 0.82): Near synonymous terms or close contextual equivalents.
    # - MEDIUM (>= 0.70): Shared conceptual domain (e.g. CI/CD vs DevOps automation).
    # - LOW (< 0.70): Weak semantic proximity, insufficient for autonomous match.
    HIGH_SEMANTIC_THRESHOLD: float = 0.82
    MEDIUM_SEMANTIC_THRESHOLD: float = 0.70
    LOW_SEMANTIC_THRESHOLD: float = 0.50

    # Initial Heuristic Weights for Job Compatibility Score (Total = 1.00)
    # Required skills carry the largest weight (0.40) to enforce candidate competency.
    INITIAL_HEURISTIC_WEIGHTS: Dict[str, float] = {
        "required_skill_weight": 0.40,
        "preferred_skill_weight": 0.15,
        "experience_weight": 0.15,
        "education_weight": 0.10,
        "certification_weight": 0.05,
        "evidence_weight": 0.10,
        "semantic_partial_weight": 0.05,
    }

    # ATS Readiness Score Weights (Total = 1.00)
    # ATS Readiness measures resume completeness, structured section quality, keyword alignment,
    # and explicit evidence density.
    ATS_READINESS_WEIGHTS: Dict[str, float] = {
        "required_keyword_coverage": 0.35,
        "evidence_density": 0.20,
        "preferred_keyword_coverage": 0.15,
        "experience_formatting": 0.15,
        "education_formatting": 0.10,
        "certification_presence": 0.05,
    }

    # Distinct Technology Pairs that MUST NEVER match via semantic similarity or partial matching
    # unless they resolve to the exact same canonical ID.
    STRICT_DISTINCT_PAIRS = [
        ("java", "javascript"),
        ("react", "react native"),
        ("amazon web services", "microsoft azure"),
        ("amazon web services", "google cloud platform"),
        ("microsoft azure", "google cloud platform"),
        ("sql", "postgresql"),
        ("sql", "mysql"),
        ("sql", "sqlite"),
        ("sql", "mongodb"),
        ("tensorflow", "pytorch"),
        ("c", "c++"),
        ("c", "c#"),
        ("c++", "c#"),
    ]


matching_config = MatchingConfig()
