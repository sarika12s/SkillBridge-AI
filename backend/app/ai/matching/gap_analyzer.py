"""Skill Gap Analyzer identifying, prioritizing, and explaining skill deficiencies."""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SkillGapAnalyzer:
    """
    Analyzes match results to isolate skill gaps, categorize priority,
    assign heuristic importance weights, and generate explainable justifications.
    """

    @staticmethod
    def identify_gaps(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filters and structures gaps from skill match records.
        """
        gaps: List[Dict[str, Any]] = []

        for m in matches:
            status = m["match_status"]
            priority = m.get("priority", "REQUIRED")
            skill_name = m["canonical_skill_name"]
            job_evidence = m.get("job_evidence")

            if status in ("MISSING_REQUIRED", "MISSING_PREFERRED"):
                weight = 2.0 if priority == "REQUIRED" else 1.0
                explanation = (
                    f"'{skill_name}' was explicitly identified as {priority.lower()} for the role, "
                    f"but is absent from the resume with no equivalent or supporting taxonomy skill detected."
                )
                gaps.append({
                    "canonical_skill_name": skill_name,
                    "priority": priority,
                    "status": status,
                    "importance_weight": weight,
                    "explanation": explanation,
                    "job_evidence": job_evidence,
                })

            elif status in ("PARTIAL_REQUIRED", "PARTIAL_PREFERRED"):
                weight = 1.5 if priority == "REQUIRED" else 0.75
                sim = m.get("similarity_score", 0.0)
                explanation = (
                    f"'{skill_name}' has partial/indirect coverage (similarity: {sim:.2f}) "
                    f"through related technology, but lacks explicit verified experience on the resume."
                )
                gaps.append({
                    "canonical_skill_name": skill_name,
                    "priority": priority,
                    "status": status,
                    "importance_weight": weight,
                    "explanation": explanation,
                    "job_evidence": job_evidence,
                })

            elif status == "RELATED_SUPPORT":
                weight = 1.0 if priority == "REQUIRED" else 0.5
                explanation = (
                    f"'{skill_name}' has supporting prerequisite or subskill coverage, but requires "
                    f"direct core proficiency to fully satisfy the requirement."
                )
                gaps.append({
                    "canonical_skill_name": skill_name,
                    "priority": priority,
                    "status": "PARTIAL_REQUIRED" if priority == "REQUIRED" else "PARTIAL_PREFERRED",
                    "importance_weight": weight,
                    "explanation": explanation,
                    "job_evidence": job_evidence,
                })

        # Sort gaps by importance weight descending (REQUIRED gaps first)
        gaps.sort(key=lambda g: g["importance_weight"], reverse=True)
        return gaps
