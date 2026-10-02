"""Requirement extraction and classification engine for Job Descriptions."""

import re
from typing import Dict, List, Any, Optional, Tuple


REQUIRED_CUES = [
    r"\bmust\s+have\b",
    r"\brequired\b",
    r"\bminimum\b",
    r"\bmandatory\b",
    r"\bessential\b",
    r"\bneeds?\s+to\s+have\b",
    r"\bproven\s+track\s+record\b",
    r"\bat\s+least\b",
]

PREFERRED_CUES = [
    r"\bpreferred\b",
    r"\bnice\s+to\s+have\b",
    r"\bbonus\b",
    r"\bplus\b",
    r"\bdesired\b",
    r"\badvantageous\b",
    r"\bhelpful\b",
    r"\boptional\b",
]


def determine_priority(text: str, section_type: str) -> Tuple[str, str]:
    """
    Determines requirement priority (REQUIRED, PREFERRED, UNKNOWN) with evidence text.
    """
    lower = text.lower()

    # 1. Explicit Preferred linguistic cues take precedence
    for cue in PREFERRED_CUES:
        m = re.search(cue, lower)
        if m:
            return "PREFERRED", f"Explicit linguistic cue: '{m.group()}'"

    # 2. Explicit Required linguistic cues
    for cue in REQUIRED_CUES:
        m = re.search(cue, lower)
        if m:
            return "REQUIRED", f"Explicit linguistic cue: '{m.group()}'"

    # 3. Section-level context
    if section_type == "PREFERRED_QUALIFICATIONS":
        return "PREFERRED", "Section context: Preferred Qualifications"

    if section_type in ("REQUIRED_QUALIFICATIONS", "TECHNICAL_SKILLS"):
        return "REQUIRED", f"Section context: {section_type}"

    return "UNKNOWN", "No explicit linguistic cue or section priority indicator"


def classify_requirement_category(text: str) -> str:
    """Classifies a requirement sentence into its primary category."""
    lower = text.lower()

    if re.search(r"\b(?:years?(?:\s+of)?\s+experience|experience\s+with|track\s+record|proven\s+experience)\b", lower):
        return "EXPERIENCE"

    if re.search(r"\b(?:bachelor'?s?|master'?s?|phd|doctorate|b\.?tech|m\.?tech|b\.?s\.?|m\.?s\.?|degree|computer\s+science|engineering)\b", lower):
        return "EDUCATION"

    if re.search(r"\b(?:certified|certification|license|credential|aws\s+certified|pmp|cissp|cka)\b", lower):
        return "CERTIFICATION"

    if re.search(r"\b(?:communication|teamwork|collaborat|leadership|problem[\s\-]solving|interpersonal)\b", lower):
        return "SOFT_SKILL"

    if re.search(r"\b(?:design|architect|implement|build|develop|maintain|lead|collaborate|participate|deliver|ensure|troubleshoot)\b", lower):
        return "RESPONSIBILITY"

    if re.search(r"\b(?:fintech|healthcare|e-commerce|banking|distributed\s+systems|cloud\s+native|cybersecurity)\b", lower):
        return "DOMAIN_KNOWLEDGE"

    return "SKILL"


def extract_structured_experience(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts explicit minimum and maximum experience years and seniority classification.
    Examples:
      '3+ years of experience' -> min: 3.0, max: None
      '2 to 4 years' -> min: 2.0, max: 4.0
      'entry-level' -> min: 0.0, max: 1.0, classification: 'ENTRY_LEVEL'
    """
    lower = text.lower()

    # Pattern: '2 to 4 years' or '2-4 years'
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|\-|–)\s*(\d+(?:\.\d+)?)\s*\+?\s*years?", lower)
    if range_match:
        min_yrs = float(range_match.group(1))
        max_yrs = float(range_match.group(2))
        return {
            "minimum_years": min_yrs,
            "maximum_years": max_yrs,
            "experience_text": text.strip(),
            "classification": _classify_seniority(min_yrs),
        }

    # Pattern: '3+ years' or 'minimum 3 years' or 'at least 5 years'
    min_match = re.search(r"(?:minimum|at\s+least|have)?\s*(\d+(?:\.\d+)?)\s*\+?\s*years?(?:\s+of\s+(?:relevant\s+)?experience)?", lower)
    if min_match:
        min_yrs = float(min_match.group(1))
        return {
            "minimum_years": min_yrs,
            "maximum_years": None,
            "experience_text": text.strip(),
            "classification": _classify_seniority(min_yrs),
        }

    # Pattern: 'entry-level' / 'fresh graduate'
    if re.search(r"\b(?:entry[\s\-]level|fresh\s+graduate|new\s+grad)\b", lower):
        return {
            "minimum_years": 0.0,
            "maximum_years": 1.0,
            "experience_text": text.strip(),
            "classification": "ENTRY_LEVEL",
        }

    return None


def _classify_seniority(years: float) -> str:
    if years <= 1.0:
        return "ENTRY_LEVEL"
    if years <= 4.0:
        return "MID_LEVEL"
    if years <= 8.0:
        return "SENIOR_LEVEL"
    return "EXECUTIVE"


def extract_structured_education(text: str, section_type: str) -> Optional[Dict[str, Any]]:
    """
    Extracts degree level, major/field, and requirement type.
    """
    lower = text.lower()
    priority, _ = determine_priority(text, section_type)

    degree_level = "UNSPECIFIED"
    if re.search(r"\b(?:ph\.?d\.?|doctorate|doctoral)\b", lower):
        degree_level = "DOCTORATE"
    elif re.search(r"\b(?:master'?s?|m\.?s\.?|m\.?tech|mba)\b", lower):
        degree_level = "MASTERS"
    elif re.search(r"\b(?:bachelor'?s?|b\.?s\.?|b\.?tech|b\.?e\.?|undergraduate)\b", lower):
        degree_level = "BACHELORS"
    elif re.search(r"\b(?:associate'?s?|diploma)\b", lower):
        degree_level = "ASSOCIATE"
    elif "degree" in lower:
        degree_level = "BACHELORS"  # Standard default in tech job listings
    if degree_level == "UNSPECIFIED":
        return None

    # Field extraction
    field = None
    field_match = re.search(r"(?:in|of)\s+([A-Za-z\s,/]+?)(?:or\s+equivalent|or\s+related|\.|\,|$)", text, re.IGNORECASE)
    if field_match:
        cand_field = field_match.group(1).strip()
        if len(cand_field) <= 60 and not re.search(r"\b(?:years|experience)\b", cand_field, re.IGNORECASE):
            field = cand_field

    return {
        "degree_level": degree_level,
        "field": field or "Computer Science or Related Field",
        "original_text": text.strip(),
        "requirement_type": priority,
    }


def extract_structured_certifications(text: str, section_type: str) -> List[Dict[str, Any]]:
    """
    Extracts explicit certification credentials mentioned in the job description.
    """
    certs = []
    priority, _ = determine_priority(text, section_type)

    patterns = [
        r"\b(AWS\s+Certified(?:\s+[A-Za-z]+)*)\b",
        r"\b(Microsoft\s+Certified(?:\s+[A-Za-z]+)*)\b",
        r"\b(Google\s+Cloud\s+Certified(?:\s+[A-Za-z]+)*)\b",
        r"\b(CISSP)\b",
        r"\b(CKA|CKAD|CKS)\b",
        r"\b(PMP|PRINCE2)\b",
        r"\b(CompTIA\s+[A-Za-z\+]+)\b",
        r"\b(Certified\s+Kubernetes\s+Administrator)\b",
    ]

    for pat in patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            cert_name = match.group(1).strip()
            certs.append({
                "name": cert_name,
                "requirement_type": priority,
            })

    return certs


def parse_job_requirements(sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts granular requirements, experience requirements, education requirements,
    and certifications from job sections.
    """
    requirements: List[Dict[str, Any]] = []
    experience_reqs: List[Dict[str, Any]] = []
    education_reqs: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []

    for sec in sections:
        sec_type = sec["section_type"]
        sec_title = sec["section_title"]
        content = sec["content_text"]

        # Split into individual bullet items or lines
        items = re.split(r"\n•\s*|\n\*\s*|\n\-\s*|\n(?=[0-9]+\.\s+)", "\n" + content)
        for raw_item in items:
            clean_item = raw_item.strip()
            # Remove leading bullets or list numbering (e.g. '1. ', '• ')
            clean_item = re.sub(r"^(?:[•\*\-\–\—]+|\d+[\.\)])\s*", "", clean_item).strip()
            if len(clean_item) < 8:
                continue

            priority, priority_evidence = determine_priority(clean_item, sec_type)
            category = classify_requirement_category(clean_item)

            requirements.append({
                "original_text": clean_item,
                "normalized_text": clean_item,
                "requirement_category": category,
                "priority": priority,
                "source_section": sec_title,
                "evidence_text": priority_evidence,
                "confidence": 0.95 if priority != "UNKNOWN" else 0.80,
            })

            # Check for structured sub-entities
            exp_data = extract_structured_experience(clean_item)
            if exp_data:
                experience_reqs.append(exp_data)

            edu_data = extract_structured_education(clean_item, sec_type)
            if edu_data:
                education_reqs.append(edu_data)

            cert_list = extract_structured_certifications(clean_item, sec_type)
            if cert_list:
                certifications.extend(cert_list)

    return {
        "requirements": requirements,
        "experience_requirements": experience_reqs,
        "education_requirements": education_reqs,
        "certifications": certifications,
    }
