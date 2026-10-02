"""Job description section segmentation and classification engine."""

import re
from typing import Dict, List, Any

# Section heading keywords and their canonical normalized category
SECTION_PATTERNS = [
    # Required / Minimum qualifications
    (
        "REQUIRED_QUALIFICATIONS",
        re.compile(
            r"^(?:minimum|basic|must[\s\-]have|required|core|mandatory)\s+(?:qualifications|requirements|skills|criteria)|"
            r"^(?:what\s+you(?:'ll|\s+will)\s+need|what\s+you\s+must\s+have|requirements|qualifications)$",
            re.IGNORECASE,
        ),
    ),
    # Preferred / Nice-to-have qualifications
    (
        "PREFERRED_QUALIFICATIONS",
        re.compile(
            r"^(?:preferred|desired|nice[\s\-]to[\s\-]have|bonus|additional|optional)\s+(?:qualifications|skills|requirements)|"
            r"^(?:what\s+sets\s+you\s+apart|bonus\s+points|nice\s+to\s+have|good\s+to\s+have|preferred)$",
            re.IGNORECASE,
        ),
    ),
    # Responsibilities
    (
        "RESPONSIBILITIES",
        re.compile(
            r"^(?:key\s+|core\s+|primary\s+)?responsibilities|"
            r"^(?:what\s+you(?:'ll|\s+will)\s+do|what\s+you\s+will\s+be\s+doing|duties|role\s+and\s+responsibilities|day\s+to\s+day)$",
            re.IGNORECASE,
        ),
    ),
    # Technical Skills
    (
        "TECHNICAL_SKILLS",
        re.compile(
            r"^(?:technical\s+skills|tech\s+stack|technologies|tools\s+(?:&|and)\s+technologies|skills\s+(?:&|and)\s+tools)$",
            re.IGNORECASE,
        ),
    ),
    # Summary / About the role
    (
        "SUMMARY",
        re.compile(
            r"^(?:about\s+(?:the\s+)?(?:role|job|position|team|us|company)|job\s+summary|position\s+overview|overview|introduction)$",
            re.IGNORECASE,
        ),
    ),
    # Experience
    (
        "EXPERIENCE",
        re.compile(r"^(?:experience|prior\s+experience|work\s+experience|background)$", re.IGNORECASE),
    ),
    # Education
    (
        "EDUCATION",
        re.compile(r"^(?:education|academic\s+background|educational\s+requirements)$", re.IGNORECASE),
    ),
    # Certifications
    (
        "CERTIFICATIONS",
        re.compile(r"^(?:certifications|licenses|credentials)$", re.IGNORECASE),
    ),
    # Benefits
    (
        "BENEFITS",
        re.compile(r"^(?:benefits|perks|what\s+we\s+offer|compensation\s+(?:&|and)\s+benefits)$", re.IGNORECASE),
    ),
]


def classify_heading(line: str) -> str:
    """Matches a line against known section heading patterns."""
    clean = re.sub(r"[:\-\–\—\*\#]+$", "", line).strip()
    clean = re.sub(r"^[0-9\.\-\*\#\s]+", "", clean).strip()

    if not clean or len(clean) > 60:
        return ""

    for section_type, pattern in SECTION_PATTERNS:
        if pattern.search(clean):
            return section_type

    return ""


def segment_job_sections(normalized_text: str) -> List[Dict[str, Any]]:
    """
    Splits job text into structured, typed sections with order indices.
    """
    if not normalized_text or not normalized_text.strip():
        return []

    lines = normalized_text.split("\n")
    sections: List[Dict[str, Any]] = []

    current_type = "SUMMARY"
    current_title = "Overview / Summary"
    current_content: List[str] = []
    order_index = 0

    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            if current_content:
                current_content.append("")
            continue

        detected_type = classify_heading(line_strip)
        if detected_type:
            # Save preceding section if it has content
            content_str = "\n".join(current_content).strip()
            if content_str:
                sections.append({
                    "section_type": current_type,
                    "section_title": current_title,
                    "content_text": content_str,
                    "order_index": order_index,
                })
                order_index += 1

            current_type = detected_type
            current_title = re.sub(r"[:\-\–\—\*\#]+$", "", line_strip).strip()
            current_content = []
        else:
            current_content.append(line_strip)

    # Append trailing section
    trailing_content = "\n".join(current_content).strip()
    if trailing_content:
        sections.append({
            "section_type": current_type,
            "section_title": current_title,
            "content_text": trailing_content,
            "order_index": order_index,
        })

    return sections
