"""Explainable Scoring Engine for SkillBridge ATS Readiness and Job Compatibility Scores."""

import logging
import math
from typing import Dict, List, Any
from app.ai.matching.config import matching_config

logger = logging.getLogger(__name__)


def clamp_score(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamps a floating point score safely between min_val and max_val, preventing NaN and Inf."""
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return float(max(min_val, min(max_val, round(value, 2))))


class ScoringEngine:
    """
    Computes explainable, reproducible scores for Job Compatibility and SkillBridge ATS Readiness.
    Strictly enforces normalization (0.0 to 100.0) and maintains granular component breakdowns.
    """

    @staticmethod
    def calculate_scores(
        matches: List[Dict[str, Any]],
        alignment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculates:
        1. Job Compatibility Score (0-100)
        2. SkillBridge ATS Readiness Score (0-100)
        3. Detailed score breakdown per component.
        """
        weights = matching_config.INITIAL_HEURISTIC_WEIGHTS
        ats_weights = matching_config.ATS_READINESS_WEIGHTS

        # 1. Required Skill Coverage
        req_matches = [m for m in matches if m.get("priority") == "REQUIRED"]
        if req_matches:
            req_scores = []
            for m in req_matches:
                m_type = m["match_type"]
                if m_type in ("DIRECT_MATCH", "ALIAS_MATCH", "TAXONOMY_EQUIVALENT"):
                    req_scores.append(100.0)
                elif m_type == "SEMANTIC_MATCH":
                    req_scores.append(85.0)
                elif m_type in ("PARTIAL_MATCH", "RELATED_SUPPORT"):
                    req_scores.append(40.0)
                else:
                    req_scores.append(0.0)
            req_score = sum(req_scores) / len(req_scores)
        else:
            req_score = 100.0  # No required skills specified in job

        # 2. Preferred Skill Coverage
        pref_matches = [m for m in matches if m.get("priority") == "PREFERRED"]
        if pref_matches:
            pref_scores = []
            for m in pref_matches:
                m_type = m["match_type"]
                if m_type in ("DIRECT_MATCH", "ALIAS_MATCH", "TAXONOMY_EQUIVALENT"):
                    pref_scores.append(100.0)
                elif m_type == "SEMANTIC_MATCH":
                    pref_scores.append(85.0)
                elif m_type in ("PARTIAL_MATCH", "RELATED_SUPPORT"):
                    pref_scores.append(40.0)
                else:
                    pref_scores.append(0.0)
            pref_score = sum(pref_scores) / len(pref_scores)
        else:
            pref_score = 100.0

        # 3. Experience Alignment Score
        exp_status = alignment.get("experience_status", "UNKNOWN")
        if exp_status == "MEETS":
            exp_score = 100.0
        elif exp_status == "UNKNOWN":
            exp_score = 50.0  # Neutral when experience duration is unquantified
        else:
            exp_score = 25.0  # Below required duration

        # 4. Education Alignment Score
        edu_status = alignment.get("education_status", "UNKNOWN")
        if edu_status == "MEETS":
            edu_score = 100.0
        elif edu_status == "PARTIAL":
            edu_score = 65.0
        elif edu_status == "UNKNOWN":
            edu_score = 80.0
        else:
            edu_score = 0.0

        # 5. Certification Alignment Score
        cert_status = alignment.get("certification_status", "UNKNOWN")
        if cert_status == "MATCHED":
            cert_score = 100.0
        elif cert_status == "PARTIAL":
            cert_score = 60.0
        elif cert_status == "UNKNOWN":
            cert_score = 100.0
        else:
            cert_score = 20.0

        # 6. Evidence Coverage Score
        # Proportion of positive skill matches supported by explicit evidence sentences
        pos_matches = [m for m in matches if m["match_type"] not in ("NO_MATCH", "UNCERTAIN")]
        if pos_matches:
            evidenced_count = sum(1 for m in pos_matches if m.get("resume_evidence") and len(m["resume_evidence"]) > 10)
            evidence_score = (evidenced_count / len(pos_matches)) * 100.0
        else:
            evidence_score = 0.0

        # 7. Semantic & Partial Proximity Score
        sim_scores = [m.get("similarity_score", 0.0) for m in matches if m.get("similarity_score") is not None]
        semantic_score = (sum(sim_scores) / len(sim_scores)) * 100.0 if sim_scores else 0.0

        # Assemble Component Breakdowns for Job Compatibility
        components = [
            {
                "component_name": "required_skill_coverage",
                "score": clamp_score(req_score),
                "max_possible": 100.0,
                "weight": weights["required_skill_weight"],
                "weighted_score": clamp_score(req_score * weights["required_skill_weight"]),
                "explanation": f"Evaluates coverage of mandatory competencies ({len([m for m in req_matches if m['match_type'] in ('DIRECT_MATCH', 'ALIAS_MATCH', 'TAXONOMY_EQUIVALENT')])}/{len(req_matches)} satisfied).",
            },
            {
                "component_name": "preferred_skill_coverage",
                "score": clamp_score(pref_score),
                "max_possible": 100.0,
                "weight": weights["preferred_skill_weight"],
                "weighted_score": clamp_score(pref_score * weights["preferred_skill_weight"]),
                "explanation": f"Evaluates bonus/secondary skills ({len([m for m in pref_matches if m['match_type'] in ('DIRECT_MATCH', 'ALIAS_MATCH', 'TAXONOMY_EQUIVALENT')])}/{len(pref_matches)} satisfied).",
            },
            {
                "component_name": "experience_alignment",
                "score": clamp_score(exp_score),
                "max_possible": 100.0,
                "weight": weights["experience_weight"],
                "weighted_score": clamp_score(exp_score * weights["experience_weight"]),
                "explanation": alignment.get("experience_explanation", "Experience duration assessment."),
            },
            {
                "component_name": "education_alignment",
                "score": clamp_score(edu_score),
                "max_possible": 100.0,
                "weight": weights["education_weight"],
                "weighted_score": clamp_score(edu_score * weights["education_weight"]),
                "explanation": alignment.get("education_explanation", "Degree level assessment."),
            },
            {
                "component_name": "certification_alignment",
                "score": clamp_score(cert_score),
                "max_possible": 100.0,
                "weight": weights["certification_weight"],
                "weighted_score": clamp_score(cert_score * weights["certification_weight"]),
                "explanation": alignment.get("certification_explanation", "Vendor credential assessment."),
            },
            {
                "component_name": "evidence_coverage",
                "score": clamp_score(evidence_score),
                "max_possible": 100.0,
                "weight": weights["evidence_weight"],
                "weighted_score": clamp_score(evidence_score * weights["evidence_weight"]),
                "explanation": f"{evidence_score:.1f}% of matched skills possess verifiable contextual sentences.",
            },
            {
                "component_name": "semantic_partial_coverage",
                "score": clamp_score(semantic_score),
                "max_possible": 100.0,
                "weight": weights["semantic_partial_weight"],
                "weighted_score": clamp_score(semantic_score * weights["semantic_partial_weight"]),
                "explanation": f"Dense embedding alignment across overall skill semantics ({semantic_score:.1f}%).",
            },
        ]

        # Calculate Overall Job Compatibility Score
        compatibility_score = clamp_score(sum(c["weighted_score"] for c in components))

        # Calculate SkillBridge ATS Readiness Score
        # ATS Readiness reflects candidate parsing clarity, keyword alignment, and formatting verification.
        ats_req = req_score * ats_weights["required_keyword_coverage"]
        ats_pref = pref_score * ats_weights["preferred_keyword_coverage"]
        ats_evid = evidence_score * ats_weights["evidence_density"]
        ats_exp = (100.0 if exp_status != "UNKNOWN" else 60.0) * ats_weights["experience_formatting"]
        ats_edu = (100.0 if edu_status != "UNKNOWN" else 70.0) * ats_weights["education_formatting"]
        ats_cert = cert_score * ats_weights["certification_presence"]

        ats_readiness_score = clamp_score(ats_req + ats_pref + ats_evid + ats_exp + ats_edu + ats_cert)

        return {
            "compatibility_score": compatibility_score,
            "ats_readiness_score": ats_readiness_score,
            "score_breakdowns": components,
        }
