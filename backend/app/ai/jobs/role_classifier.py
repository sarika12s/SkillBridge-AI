"""Role classifier mapping job title to canonical career roles."""

import re
from typing import Tuple

ROLE_PATTERNS = [
    ("Machine Learning Engineer", re.compile(r"\b(?:machine\s+learning|ml|ai|artificial\s+intelligence)(?:\s+software|\s+systems)?\s+(?:engineer|specialist|developer)\b", re.IGNORECASE), 0.95),
    ("Data Scientist", re.compile(r"\b(?:data\s+scientist|applied\s+scientist)\b", re.IGNORECASE), 0.95),
    ("Data Analyst", re.compile(r"\b(?:data\s+analyst|bi\s+analyst|business\s+intelligence\s+analyst)\b", re.IGNORECASE), 0.90),
    ("DevOps Engineer", re.compile(r"\b(?:devops|sre|site\s+reliability\s+engineer|platform\s+engineer|infrastructure\s+engineer)\b", re.IGNORECASE), 0.95),
    ("Cloud Architect", re.compile(r"\b(?:cloud\s+(?:architect|solutions\s+architect|cloud\s+engineer))\b", re.IGNORECASE), 0.90),
    ("Frontend Developer", re.compile(r"\b(?:frontend|front[\s\-]end|ui|client[\s\-]side)(?:\s+software|\s+systems)?\s+(?:engineer|developer)\b", re.IGNORECASE), 0.95),
    ("Backend Developer", re.compile(r"\b(?:backend|back[\s\-]end|server[\s\-]side)(?:\s+software|\s+systems)?\s+(?:engineer|developer)\b", re.IGNORECASE), 0.95),
    ("Full Stack Developer", re.compile(r"\b(?:full[\s\-]stack|fullstack)(?:\s+software|\s+systems)?\s+(?:engineer|developer)\b", re.IGNORECASE), 0.95),
    ("Mobile App Developer", re.compile(r"\b(?:mobile|ios|android|react\s+native)(?:\s+software|\s+systems)?\s+(?:engineer|developer)\b", re.IGNORECASE), 0.95),
    ("Cybersecurity Engineer", re.compile(r"\b(?:security|cybersecurity|infosec)\s+(?:engineer|analyst)\b", re.IGNORECASE), 0.90),
    ("Quality Assurance Engineer", re.compile(r"\b(?:qa|quality\s+assurance|test|sdet)\s+(?:engineer|analyst)\b", re.IGNORECASE), 0.90),
    ("Software Engineer", re.compile(r"\b(?:software\s+(?:engineer|developer)|systems\s+engineer|programmer)\b", re.IGNORECASE), 0.85),
]


def classify_job_role(title: str, summary: str = "") -> Tuple[str, float, str]:
    """
    Classifies a job title into a canonical technical role with confidence and method.
    Returns (normalized_role, confidence, classification_method).
    """
    if not title or not title.strip():
        return "UNKNOWN", 0.0, "RULE_BASED"

    clean_title = title.strip()

    # 1. Match title directly
    for role_name, pattern, confidence in ROLE_PATTERNS:
        if pattern.search(clean_title):
            return role_name, confidence, "RULE_BASED"

    # 2. Check summary preamble if title was non-standard (e.g. "Associate Technical Lead")
    if summary:
        for role_name, pattern, confidence in ROLE_PATTERNS:
            if pattern.search(summary[:300]):
                return role_name, round(confidence * 0.80, 2), "SUMMARY_HEURISTIC"

    # 3. Default fallback if contains tech indicators
    if re.search(r"\b(?:engineer|developer|architect|consultant|analyst)\b", clean_title, re.IGNORECASE):
        return "Software Engineer", 0.60, "FALLBACK_ROLE"

    return "UNKNOWN", 0.30, "LOW_CONFIDENCE"
