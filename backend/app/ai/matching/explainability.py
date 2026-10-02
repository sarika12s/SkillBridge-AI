"""Dedicated Explainability Engine generating human-interpretable assessment narratives."""

from typing import Dict, List, Any


class ExplainabilityEngine:
    """
    Generates granular, transparent justifications for match outcomes.
    Discloses positive drivers, bottleneck penalties, and factual uncertainties
    without black-box or generic claims.
    """

    @staticmethod
    def generate_explanation(
        matches: List[Dict[str, Any]],
        gaps: List[Dict[str, Any]],
        alignment: Dict[str, Any],
        scores: Dict[str, Any],
        job_title: str,
    ) -> Dict[str, Any]:
        """
        Synthesizes match signals into structured explainability reports.
        """
        strengths: List[str] = []
        critical_gaps: List[str] = []
        positive_factors: List[str] = []
        negative_factors: List[str] = []
        uncertainties: List[str] = []

        # Analyze Skill Matches
        direct_matches = [m for m in matches if m["match_type"] in ("DIRECT_MATCH", "ALIAS_MATCH", "TAXONOMY_EQUIVALENT")]
        for m in direct_matches:
            if m.get("priority") == "REQUIRED":
                strengths.append(
                    f"Directly verified required competency: '{m['canonical_skill_name']}'."
                )

        if len(direct_matches) > 0:
            positive_factors.append(
                f"Demonstrated {len(direct_matches)} direct canonical skill matches against job requirements."
            )

        # Analyze Gaps
        req_gaps = [g for g in gaps if g.get("priority") == "REQUIRED"]
        for g in req_gaps:
            critical_gaps.append(
                f"Missing mandatory skill: '{g['canonical_skill_name']}' is required for {job_title}."
            )
            negative_factors.append(
                f"Score reduced due to absence of required skill '{g['canonical_skill_name']}'."
            )

        pref_gaps = [g for g in gaps if g.get("priority") == "PREFERRED"]
        if pref_gaps:
            negative_factors.append(
                f"{len(pref_gaps)} preferred/bonus skills were not demonstrated on the resume."
            )

        # Analyze Alignment Factors
        exp_status = alignment.get("experience_status")
        if exp_status == "MEETS":
            positive_factors.append(
                f"Work experience duration ({alignment.get('resume_years')} yrs) satisfies required {alignment.get('required_years')} yrs."
            )
        elif exp_status == "BELOW_REQUIREMENT":
            negative_factors.append(
                f"Stated experience ({alignment.get('resume_years')} yrs) is below the requested {alignment.get('required_years')} yrs."
            )
        elif exp_status == "UNKNOWN":
            uncertainties.append(
                "Candidate's exact experience duration could not be factually determined from resume text."
            )

        edu_status = alignment.get("education_status")
        if edu_status == "MEETS":
            positive_factors.append(
                f"Academic credentials ({alignment.get('resume_degree')}) align with position requirements."
            )
        elif edu_status == "MISSING":
            negative_factors.append(
                f"Mandatory educational degree ({alignment.get('required_degree')}) was not identified."
            )

        # Synthesize Summary Narrative
        comp_score = scores.get("compatibility_score", 0.0)
        ats_score = scores.get("ats_readiness_score", 0.0)

        narrative_parts = [
            f"The candidate demonstrates an analytical Job Compatibility Score of {comp_score:.1f}% "
            f"and a SkillBridge ATS Readiness Score of {ats_score:.1f}% for the '{job_title}' position.",
        ]

        if direct_matches:
            match_names = [m["canonical_skill_name"] for m in direct_matches[:4]]
            narrative_parts.append(
                f"Strongest alignment is shown in core competencies including: {', '.join(match_names)}."
            )

        if req_gaps:
            gap_names = [g["canonical_skill_name"] for g in req_gaps[:3]]
            narrative_parts.append(
                f"Primary compatibility bottlenecks stem from unfulfilled mandatory requirements: {', '.join(gap_names)}."
            )
        else:
            narrative_parts.append("All explicitly mandatory skill requirements have verified coverage.")

        if uncertainties:
            narrative_parts.append(
                f"Note: {uncertainties[0]}"
            )

        summary_narrative = " ".join(narrative_parts)

        return {
            "summary_explanation": summary_narrative,
            "strengths": strengths,
            "critical_gaps": critical_gaps,
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "uncertainties": uncertainties,
        }
