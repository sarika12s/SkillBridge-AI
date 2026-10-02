"""Career Role Compatibility Engine.

Calculates multi-role analytical compatibility between candidate resume skills and standardized occupations.
Provides explainable score breakdowns and factual justifications without black-box guessing.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.career import Occupation


class CareerEngine:
    """Calculates explainable career role compatibility for a resume against standardized occupations."""

    WEIGHT_REQUIRED = 0.50
    WEIGHT_PREFERRED = 0.20
    WEIGHT_EVIDENCE = 0.15
    WEIGHT_DOMAIN = 0.15

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def evaluate_role_compatibility(
        self,
        resume: Resume,
        occupations: List[Occupation],
    ) -> List[Dict[str, Any]]:
        """
        Evaluates a candidate's resume against all provided occupations.
        Returns a list of evaluated roles sorted descending by compatibility_score.
        """
        candidate_skills = self._extract_candidate_skill_map(resume)
        results = []

        for occ in occupations:
            eval_result = self._score_single_occupation(resume, occ, candidate_skills)
            results.append(eval_result)

        # Sort descending by compatibility_score
        results.sort(key=lambda r: r["compatibility_score"], reverse=True)
        return results

    def _extract_candidate_skill_map(self, resume: Resume) -> Dict[str, Dict[str, Any]]:
        """
        Extracts candidate canonical skills and evidence context from resume.
        Returns map: normalized_name -> {canonical_name, category, evidence_count, has_project_or_exp}
        """
        skill_map: Dict[str, Dict[str, Any]] = {}

        for rs in getattr(resume, "skills", []):
            canonical_name = (
                getattr(rs, "canonical_skill_name", None)
                or (rs.skill.name if getattr(rs, "skill", None) else getattr(rs, "raw_skill_text", "Unknown"))
            )
            norm_name = canonical_name.lower().strip()
            
            section_type = getattr(rs, "source_section", getattr(rs, "section_type", "SKILLS")) or "SKILLS"
            has_experience = section_type.upper() in ["EXPERIENCE", "PROJECTS", "WORK_EXPERIENCE"]

            if norm_name not in skill_map:
                skill_map[norm_name] = {
                    "canonical_name": canonical_name,
                    "category": getattr(getattr(rs, "skill", None), "category", "TECHNICAL_SKILL"),
                    "mentions": 1,
                    "has_experience": has_experience,
                }
            else:
                skill_map[norm_name]["mentions"] += 1
                if has_experience:
                    skill_map[norm_name]["has_experience"] = True

        return skill_map

    def _score_single_occupation(
        self,
        resume: Resume,
        occ: Occupation,
        candidate_skills: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculates component-based compatibility score for one occupation."""
        required_skills = []
        preferred_skills = []

        for os in getattr(occ, "skills", []):
            sk_name = os.skill.name if getattr(os, "skill", None) else "Unknown"
            if os.requirement_type == "REQUIRED":
                required_skills.append((sk_name, os.importance_weight))
            else:
                preferred_skills.append((sk_name, os.importance_weight))

        matched_required = []
        missing_required = []
        for sk_name, weight in required_skills:
            norm = sk_name.lower().strip()
            if norm in candidate_skills:
                matched_required.append(sk_name)
            else:
                missing_required.append(sk_name)

        matched_preferred = []
        missing_preferred = []
        for sk_name, weight in preferred_skills:
            norm = sk_name.lower().strip()
            if norm in candidate_skills:
                matched_preferred.append(sk_name)
            else:
                missing_preferred.append(sk_name)

        # 1. Required Skills Score (0 - 100)
        req_score = (
            (len(matched_required) / len(required_skills)) * 100.0
            if required_skills
            else 100.0
        )
        req_weighted = round(req_score * self.WEIGHT_REQUIRED, 2)

        # 2. Preferred Skills Score (0 - 100)
        pref_score = (
            (len(matched_preferred) / len(preferred_skills)) * 100.0
            if preferred_skills
            else 100.0
        )
        pref_weighted = round(pref_score * self.WEIGHT_PREFERRED, 2)

        # 3. Evidence & Practical Application Score (0 - 100)
        all_matched = matched_required + matched_preferred
        if all_matched:
            practical_count = sum(
                1 for s in all_matched if candidate_skills.get(s.lower().strip(), {}).get("has_experience", False)
            )
            evidence_score = (practical_count / len(all_matched)) * 100.0
            # Give baseline credit of at least 50% if skills exist
            evidence_score = max(50.0, evidence_score)
        else:
            evidence_score = 0.0
        evidence_weighted = round(evidence_score * self.WEIGHT_EVIDENCE, 2)

        # 4. Domain Specialization Fit (0 - 100)
        domain_score = self._calculate_domain_fit(occ.category, candidate_skills)
        domain_weighted = round(domain_score * self.WEIGHT_DOMAIN, 2)

        total_score = round(req_weighted + pref_weighted + evidence_weighted + domain_weighted, 1)
        total_score = max(0.0, min(100.0, total_score))

        # Explainable components
        components = [
            {
                "component_name": "Required Skills Match",
                "score": round(req_score, 1),
                "weight": self.WEIGHT_REQUIRED,
                "weighted_score": req_weighted,
                "explanation": f"Candidate demonstrates {len(matched_required)} of {len(required_skills)} required core competencies.",
            },
            {
                "component_name": "Preferred Skills Match",
                "score": round(pref_score, 1),
                "weight": self.WEIGHT_PREFERRED,
                "weighted_score": pref_weighted,
                "explanation": f"Candidate demonstrates {len(matched_preferred)} of {len(preferred_skills)} preferred competencies.",
            },
            {
                "component_name": "Practical Evidence Alignment",
                "score": round(evidence_score, 1),
                "weight": self.WEIGHT_EVIDENCE,
                "weighted_score": evidence_weighted,
                "explanation": f"Evaluates practical validation across project work and verifiable experience context.",
            },
            {
                "component_name": "Domain Specialization Fit",
                "score": round(domain_score, 1),
                "weight": self.WEIGHT_DOMAIN,
                "weighted_score": domain_weighted,
                "explanation": f"Measures candidate background alignment with the '{occ.category}' professional domain.",
            },
        ]

        # Strengths & Gaps
        strengths = matched_required[:5] + [s for s in matched_preferred if s not in matched_required][:3]
        skill_gaps = missing_required + missing_preferred

        summary = self._generate_role_narrative(
            occ.title, total_score, matched_required, required_skills, missing_required, missing_preferred
        )

        return {
            "occupation_id": occ.id,
            "occupation_title": occ.title,
            "occupation_code": occ.code,
            "category": occ.category,
            "compatibility_score": total_score,
            "summary_explanation": summary,
            "components": components,
            "strengths": strengths,
            "skill_gaps": skill_gaps,
            "matched_skills_count": len(all_matched),
            "total_skills_count": len(required_skills) + len(preferred_skills),
        }

    def _calculate_domain_fit(
        self,
        target_category: str,
        candidate_skills: Dict[str, Dict[str, Any]],
    ) -> float:
        """Calculates domain category overlap score."""
        if not candidate_skills:
            return 0.0

        target_norm = target_category.upper().replace(" ", "_")
        domain_matches = 0
        total_skills = len(candidate_skills)

        category_mapping = {
            "SOFTWARE_DEVELOPMENT": ["PROGRAMMING_LANGUAGE", "FRAMEWORK", "DATABASE", "API", "VERSION_CONTROL"],
            "ARTIFICIAL_INTELLIGENCE": ["AI_ML", "DATA_ENGINEERING", "PROGRAMMING_LANGUAGE", "DATA_SCIENCE"],
            "CLOUD_DEVOPS": ["CLOUD_DEVOPS", "CONTAINERIZATION", "LINUX", "ORCHESTRATION", "CI_CD"],
            "DATA_SCIENCE": ["DATA_SCIENCE", "DATA_ENGINEERING", "AI_ML", "DATABASE", "STATISTICS"],
        }

        relevant_categories = category_mapping.get(target_norm, ["TECHNICAL_SKILL"])

        for sk_data in candidate_skills.values():
            cat = sk_data.get("category", "").upper()
            if cat in relevant_categories or cat == target_norm:
                domain_matches += 1

        if total_skills == 0:
            return 50.0
        
        ratio = domain_matches / total_skills
        # Map ratio to 40 - 100 scale for reasonable distribution
        return round(min(100.0, max(30.0, ratio * 120.0)), 1)

    def _generate_role_narrative(
        self,
        title: str,
        score: float,
        matched_required: List[str],
        required_skills: List[Any],
        missing_required: List[str],
        missing_preferred: List[str],
    ) -> str:
        """Generates clear, analytical narrative describing candidate readiness for the role."""
        if score >= 80.0:
            fit_level = "strong analytical match"
        elif score >= 60.0:
            fit_level = "moderate readiness match"
        elif score >= 40.0:
            fit_level = "developing foundation"
        else:
            fit_level = "emerging early alignment"

        narrative = f"Candidate displays {fit_level} for {title} with an overall score of {score}%."

        if matched_required:
            demonstrated = ", ".join(matched_required[:4])
            narrative += f" Key strengths include demonstrated proficiency in {demonstrated}."

        if missing_required:
            missing_str = ", ".join(missing_required[:3])
            narrative += f" Primary skill gaps to address for full qualification: {missing_str}."
        elif missing_preferred:
            pref_str = ", ".join(missing_preferred[:3])
            narrative += f" To stand out against senior competition, recommended enhancements: {pref_str}."

        return narrative
