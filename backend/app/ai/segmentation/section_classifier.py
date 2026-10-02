"""Structured section demarcation and normalization engine for resumes."""

import re
from typing import List, Dict, Any, Tuple

# Canonical mapping of normalized section types to regex patterns
SECTION_HEADER_PATTERNS = {
    "SUMMARY": re.compile(
        r"^(professional\s+summary|executive\s+summary|career\s+summary|career\s+objective|objective|about\s+me|profile|professional\s+profile|personal\s+profile)$",
        re.IGNORECASE,
    ),
    "EDUCATION": re.compile(
        r"^(education|academic\s+qualifications?|academic\s+background|educational\s+background|academic\s+credentials|academics|qualifications)$",
        re.IGNORECASE,
    ),
    "EXPERIENCE": re.compile(
        r"^(work\s+experience|professional\s+experience|employment\s+history|work\s+history|professional\s+background|experience|relevant\s+experience|career\s+history|internships?)$",
        re.IGNORECASE,
    ),
    "PROJECTS": re.compile(
        r"^(projects|academic\s+projects|personal\s+projects|technical\s+projects|key\s+projects|capstone\s+projects?|selected\s+projects)$",
        re.IGNORECASE,
    ),
    "SKILLS": re.compile(
        r"^(technical\s+skills|core\s+competencies|key\s+skills|skills\s*(&|and)\s*abilities|skills|technologies|tech\s+stack|areas\s+of\s+expertise|professional\s+skills)$",
        re.IGNORECASE,
    ),
    "CERTIFICATIONS": re.compile(
        r"^(certifications?|licenses?\s*(&|and)\s*certifications?|certificates?|professional\s+certifications?|accreditations?)$",
        re.IGNORECASE,
    ),
    "ACHIEVEMENTS": re.compile(
        r"^(achievements|honors?\s*(&|and)\s*awards?|awards?(\s+and\s+honors?)?|honors?|accomplishments?|key\s+achievements)$",
        re.IGNORECASE,
    ),
    "PUBLICATIONS": re.compile(
        r"^(publications|research\s+papers?|papers|conference\s+proceedings)$",
        re.IGNORECASE,
    ),
    "LANGUAGES": re.compile(
        r"^(languages?|language\s+proficiency)$",
        re.IGNORECASE,
    ),
    "INTERESTS": re.compile(
        r"^(interests?|hobbies|extracurricular\s+activities|extracurriculars)$",
        re.IGNORECASE,
    ),
}


def is_potential_heading(line: str) -> Tuple[bool, str | None, float]:
    """
    Determines if a line is a section heading.
    Returns:
        (is_heading, normalized_section_type, confidence_score)
    """
    clean_line = line.strip().rstrip(":-_#")
    if not clean_line or len(clean_line) > 55 or len(clean_line.split()) > 6:
        return False, None, 0.0

    # Test exact pattern matching
    for sec_type, pattern in SECTION_HEADER_PATTERNS.items():
        if pattern.match(clean_line):
            return True, sec_type, 1.0

    # Test secondary containment heuristic for title case / uppercase short lines
    words = clean_line.lower().split()
    if clean_line.isupper() or clean_line.istitle():
        if "experience" in words or "employment" in words:
            return True, "EXPERIENCE", 0.85
        if "education" in words or "academic" in words:
            return True, "EDUCATION", 0.85
        if "project" in words or "projects" in words:
            return True, "PROJECTS", 0.85
        if "skill" in words or "skills" in words:
            return True, "SKILLS", 0.85
        if "certification" in words or "certifications" in words:
            return True, "CERTIFICATIONS", 0.85
        if "award" in words or "awards" in words or "honors" in words:
            return True, "ACHIEVEMENTS", 0.85

    return False, None, 0.0


def segment_resume_sections(full_text: str) -> List[Dict[str, Any]]:
    """
    Segments full resume text into structured, normalized section records.
    Preceding text before the first identified section is classified as CONTACT.
    """
    lines = full_text.split("\n")
    sections: List[Dict[str, Any]] = []

    current_type = "CONTACT"
    current_title = "Contact Information"
    current_confidence = 1.0
    current_content: List[str] = []
    order_idx = 0

    for line in lines:
        stripped = line.strip()
        is_hdr, norm_type, conf = is_potential_heading(stripped)

        if is_hdr and norm_type:
            # Commit the previous section if it has content
            content_text = "\n".join(current_content).strip()
            if content_text:
                sections.append({
                    "section_type": current_type,
                    "section_title": current_title,
                    "content_text": content_text,
                    "order_index": order_idx,
                    "confidence_score": current_confidence,
                })
                order_idx += 1

            # Start new section
            current_type = norm_type
            current_title = stripped
            current_confidence = conf
            current_content = []
        else:
            if stripped:
                current_content.append(stripped)

    # Commit the final remaining section
    content_text = "\n".join(current_content).strip()
    if content_text:
        sections.append({
            "section_type": current_type,
            "section_title": current_title,
            "content_text": content_text,
            "order_index": order_idx,
            "confidence_score": current_confidence,
        })

    return sections
