"""Structured Alignment Evaluators for Experience, Education, and Certifications."""

import logging
import re
from typing import Dict, List, Optional, Any
from app.models.resume import Resume, ResumeExperience, ResumeCertification
from app.models.job import (
    Job,
    JobExperienceRequirement,
    JobEducationRequirement,
    JobCertification,
)

logger = logging.getLogger(__name__)

DEGREE_HIERARCHY = {
    "DOCTORATE": 4,
    "MASTERS": 3,
    "BACHELORS": 2,
    "ASSOCIATE": 1,
    "UNSPECIFIED": 0,
}


class AlignmentEvaluator:
    """
    Evaluates explicit structured requirements (Experience, Education, Certifications)
    between a Resume and a Job Description. Strictly adheres to factual evidence without
    fabricating unstated data.
    """

    @staticmethod
    def evaluate_experience(
        resume: Resume,
        job_experience_reqs: List[JobExperienceRequirement],
    ) -> Dict[str, Any]:
        """
        Evaluates candidate work experience duration against job requirements.
        Returns:
            MEETS: Candidate meets or exceeds minimum years.
            BELOW_REQUIREMENT: Candidate years are explicitly stated and below requirement.
            UNKNOWN: Insufficient explicit duration data available on resume.
        """
        if not job_experience_reqs:
            return {
                "experience_status": "MEETS",
                "experience_explanation": "No minimum years of experience were explicitly required by the job.",
                "resume_years": None,
                "required_years": None,
            }

        req = job_experience_reqs[0]
        min_required = req.minimum_years or 0.0

        # Extract explicit duration from resume experience entries or text
        candidate_years: Optional[float] = None

        # Check explicit experience entries if present
        exp_entries = getattr(resume, "experience", None) or getattr(resume, "experiences", None)
        if exp_entries:
            total_duration_years = 0.0
            for exp in exp_entries:
                # Look for year numbers in experience descriptions
                title_val = getattr(exp, 'job_title', '') or getattr(exp, 'title', '')
                comp_val = getattr(exp, 'company_name', '') or getattr(exp, 'company', '')
                desc_val = getattr(exp, 'description', '') or ''
                text = f"{title_val} {comp_val} {desc_val}"
                yr_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", text, re.IGNORECASE)
                if yr_match:
                    total_duration_years += float(yr_match.group(1))

            if total_duration_years > 0:
                candidate_years = total_duration_years

        # If not found in structured items, search entire resume text for experience statement
        if candidate_years is None and resume.raw_text:
            text_match = re.search(
                r"(\d+(?:\.\d+)?)\s*\+?\s*years?(?:\s+of)?(?:\s+[\w\s]{0,50})?\s+experience",
                resume.raw_text,
                re.IGNORECASE,
            )
            if text_match:
                candidate_years = float(text_match.group(1))

        if candidate_years is None:
            return {
                "experience_status": "UNKNOWN",
                "experience_explanation": (
                    f"Job requires {min_required:g}+ years of experience ({req.classification}). "
                    f"Candidate's exact experience duration is not explicitly quantified on the resume."
                ),
                "resume_years": None,
                "required_years": min_required,
            }

        if candidate_years >= min_required:
            return {
                "experience_status": "MEETS",
                "experience_explanation": (
                    f"Demonstrated {candidate_years:g} years of experience, meeting the required {min_required:g}+ years."
                ),
                "resume_years": candidate_years,
                "required_years": min_required,
            }
        else:
            return {
                "experience_status": "BELOW_REQUIREMENT",
                "experience_explanation": (
                    f"Demonstrated {candidate_years:g} years of experience is below the requested {min_required:g}+ years."
                ),
                "resume_years": candidate_years,
                "required_years": min_required,
            }

    @staticmethod
    def evaluate_education(
        resume: Resume,
        job_education_reqs: List[JobEducationRequirement],
    ) -> Dict[str, Any]:
        """
        Evaluates academic degrees and fields of study between resume and job.
        Returns:
            MEETS: Degree level and field align.
            PARTIAL: Degree level meets, but specific field is not clearly matched.
            MISSING: Required degree level is missing from resume.
            UNKNOWN: No education requirements or ambiguous records.
        """
        if not job_education_reqs:
            return {
                "education_status": "MEETS",
                "education_explanation": "No formal academic degree was explicitly mandated.",
                "resume_degree": None,
                "required_degree": None,
            }

        edu_req = job_education_reqs[0]
        req_level = (edu_req.degree_level or "BACHELORS").upper()
        req_rank = DEGREE_HIERARCHY.get(req_level, 2)
        req_field = edu_req.field or ""

        # Extract candidate degree from resume
        resume_level = "UNSPECIFIED"
        raw_text_lower = (resume.raw_text or "").lower()

        if re.search(r"\b(?:ph\.?d\.?|doctorate)\b", raw_text_lower):
            resume_level = "DOCTORATE"
        elif re.search(r"\b(?:master'?s?|m\.?s\.?|m\.?tech|mba)\b", raw_text_lower):
            resume_level = "MASTERS"
        elif re.search(r"\b(?:bachelor'?s?|b\.?s\.?|b\.?tech|b\.?e\.?|undergraduate)\b", raw_text_lower):
            resume_level = "BACHELORS"
        elif re.search(r"\b(?:associate'?s?|diploma)\b", raw_text_lower):
            resume_level = "ASSOCIATE"

        cand_rank = DEGREE_HIERARCHY.get(resume_level, 0)

        if cand_rank == 0:
            return {
                "education_status": "MISSING" if edu_req.requirement_type == "REQUIRED" else "UNKNOWN",
                "education_explanation": (
                    f"Job requires {req_level} degree"
                    + (f" in {req_field}" if req_field else "")
                    + ", but no formal degree was found on the resume."
                ),
                "resume_degree": None,
                "required_degree": req_level,
            }

        if cand_rank >= req_rank:
            # Check field alignment if specified
            field_match = True
            if req_field and len(req_field) > 3:
                field_match = bool(re.search(re.escape(req_field.lower()), raw_text_lower)) or bool(
                    re.search(r"\b(?:computer|software|engineering|science|information)\b", raw_text_lower)
                )

            if field_match:
                return {
                    "education_status": "MEETS",
                    "education_explanation": (
                        f"Candidate holds a {resume_level} degree, satisfying the required {req_level} qualification."
                    ),
                    "resume_degree": resume_level,
                    "required_degree": req_level,
                }
            else:
                return {
                    "education_status": "PARTIAL",
                    "education_explanation": (
                        f"Candidate holds a {resume_level} degree, but the specific requested field ('{req_field}') is unverified."
                    ),
                    "resume_degree": resume_level,
                    "required_degree": req_level,
                }
        else:
            return {
                "education_status": "PARTIAL",
                "education_explanation": (
                    f"Candidate holds an {resume_level} degree, which is below the requested {req_level} level."
                ),
                "resume_degree": resume_level,
                "required_degree": req_level,
            }

    @staticmethod
    def evaluate_certifications(
        resume: Resume,
        job_certifications: List[JobCertification],
    ) -> Dict[str, Any]:
        """
        Evaluates vendor certifications between resume and job.
        Returns:
            MATCHED: All required certifications present.
            PARTIAL: Some certifications present.
            MISSING: Certifications missing.
            UNKNOWN: None required.
        """
        if not job_certifications:
            return {
                "certification_status": "MATCHED",
                "certification_explanation": "No certifications were required for this position.",
                "matched_certifications": [],
                "missing_certifications": [],
            }

        resume_certs = [c.name.lower() for c in (resume.certifications or [])]
        raw_text_lower = (resume.raw_text or "").lower()

        matched = []
        missing = []

        for j_cert in job_certifications:
            c_name = j_cert.name
            c_lower = c_name.lower()

            # Check if name is in structured certifications or raw text
            is_matched = any(c_lower in rc for rc in resume_certs) or (c_lower in raw_text_lower)
            if not is_matched:
                # Check acronyms (e.g. AWS Certified, CKA, PMP)
                keywords = [w for w in c_lower.split() if len(w) > 3]
                if keywords and all(w in raw_text_lower for w in keywords):
                    is_matched = True

            if is_matched:
                matched.append(c_name)
            else:
                missing.append(c_name)

        if not missing:
            status = "MATCHED"
            explanation = f"All requested certifications verified: {', '.join(matched)}."
        elif matched:
            status = "PARTIAL"
            explanation = f"Partial certification coverage: Matched {len(matched)}, missing {len(missing)}."
        else:
            status = "MISSING"
            explanation = f"Requested certifications missing: {', '.join(missing)}."

        return {
            "certification_status": status,
            "certification_explanation": explanation,
            "matched_certifications": matched,
            "missing_certifications": missing,
        }
