"""Deterministic entity and contact information extractor for resumes."""

import re
from typing import Dict, Any, List, Optional

# Regular expression patterns for contact details
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
)
PHONE_REGEX = re.compile(
    r"(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?|\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
)
LINKEDIN_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9_-]+)/?",
    re.IGNORECASE,
)
GITHUB_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+)/?",
    re.IGNORECASE,
)
URL_REGEX = re.compile(
    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)",
    re.IGNORECASE,
)
DATE_RANGE_REGEX = re.compile(
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4})\s*(?:-|–|—|to)\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|Present|Current)",
    re.IGNORECASE,
)


def extract_contact_information(full_text: str, contact_section_text: str = "") -> Dict[str, Optional[str]]:
    """
    Extracts name, email, phone, location, LinkedIn, GitHub, and portfolio URLs.
    Does not fabricate or guess any values.
    """
    search_scope = f"{contact_section_text}\n{full_text[:1500]}"

    # Extract Email
    email_match = EMAIL_REGEX.search(search_scope)
    email = email_match.group(0).strip() if email_match else None

    # Extract Phone
    phone = None
    for match in PHONE_REGEX.finditer(search_scope):
        candidate_phone = match.group(0).strip()
        # Ensure it has at least 7 digits to avoid false positives with dates or numbers
        digit_count = sum(1 for c in candidate_phone if c.isdigit())
        if 7 <= digit_count <= 15:
            phone = candidate_phone
            break

    # Extract LinkedIn
    linkedin_match = LINKEDIN_REGEX.search(search_scope)
    linkedin_url = linkedin_match.group(0).strip() if linkedin_match else None
    if linkedin_url and not linkedin_url.startswith("http"):
        linkedin_url = f"https://{linkedin_url}"

    # Extract GitHub
    github_match = GITHUB_REGEX.search(search_scope)
    github_url = github_match.group(0).strip() if github_match else None
    if github_url and not github_url.startswith("http"):
        github_url = f"https://{github_url}"

    # Extract Portfolio / Generic URLs (excluding LinkedIn and GitHub)
    portfolio_url = None
    for url_match in URL_REGEX.finditer(search_scope):
        url = url_match.group(0).strip()
        if "linkedin.com" not in url.lower() and "github.com" not in url.lower():
            portfolio_url = url
            break

    # Extract Candidate Name (heuristically from the earliest non-empty line)
    name = None
    lines = search_scope.split("\n")
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
        # Skip if contains email, URL, phone, or obvious section header keywords
        if (
            "@" in cleaned_line
            or "http" in cleaned_line.lower()
            or "github" in cleaned_line.lower()
            or "linkedin" in cleaned_line.lower()
            or sum(1 for c in cleaned_line if c.isdigit()) > 2
            or len(cleaned_line) > 50
        ):
            continue
        # Clean potential title or label prefix
        cleaned_line = re.sub(r"^(name|resume|curriculum vitae|cv)\s*[:|-]?\s*", "", cleaned_line, flags=re.IGNORECASE).strip()
        # Verify it consists of alphabetic characters and standard name separators
        if re.match(r"^[A-Za-z\s.'-]+$", cleaned_line) and len(cleaned_line.split()) in (2, 3, 4):
            name = cleaned_line
            break

    # Extract Location Heuristic (city, state/country)
    location = None
    location_regex = re.compile(r"\b([A-Z][a-zA-Z\s]+,\s*[A-Z]{2,}(?:\s+\d{5})?|[A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)\b")
    loc_match = location_regex.search(search_scope)
    if loc_match:
        cand_loc = loc_match.group(1).strip()
        # Exclude common university or degree matches
        if not any(w in cand_loc.lower() for w in ["university", "college", "bachelor", "master", "technology"]):
            location = cand_loc

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "linkedin_url": linkedin_url,
        "github_url": github_url,
        "portfolio_url": portfolio_url,
    }


def extract_structured_experience(experience_text: str) -> List[Dict[str, Any]]:
    """Extracts job entries, dates, company names, and descriptions from the EXPERIENCE section."""
    if not experience_text or not experience_text.strip():
        return []

    entries: List[Dict[str, Any]] = []
    paragraphs = [p.strip() for p in experience_text.split("\n\n") if p.strip()]

    for para in paragraphs:
        lines = [l.strip() for l in para.split("\n") if l.strip()]
        if not lines:
            continue

        header_line = lines[0]
        date_match = DATE_RANGE_REGEX.search(header_line)
        start_date, end_date = None, None
        is_current = False

        if date_match:
            start_date = date_match.group(1).strip()
            end_date = date_match.group(2).strip()
            if "present" in end_date.lower() or "current" in end_date.lower():
                is_current = True

        # Attempt to split Company and Title (e.g. "Software Engineer at Google" or "Google | Software Engineer")
        clean_header = DATE_RANGE_REGEX.sub("", header_line).strip(" |-—–")
        company, title = clean_header, "Professional Role"
        if " at " in clean_header:
            parts = clean_header.split(" at ", 1)
            title, company = parts[0].strip(), parts[1].strip()
        elif "|" in clean_header:
            parts = clean_header.split("|", 1)
            company, title = parts[0].strip(), parts[1].strip()
        elif " - " in clean_header:
            parts = clean_header.split(" - ", 1)
            company, title = parts[0].strip(), parts[1].strip()

        desc_lines = lines[1:] if len(lines) > 1 else []
        description = "\n".join(desc_lines) if desc_lines else None

        entries.append({
            "company_name": company or "Organization",
            "job_title": title or "Role",
            "location": None,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "is_current": is_current,
        })

    return entries


def extract_structured_projects(projects_text: str) -> List[Dict[str, Any]]:
    """Extracts project records, tech stacks, and descriptions from the PROJECTS section."""
    if not projects_text or not projects_text.strip():
        return []

    projects: List[Dict[str, Any]] = []
    blocks = [b.strip() for b in projects_text.split("\n\n") if b.strip()]

    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        first_line = lines[0]
        # Check if project contains technologies in parentheses or after colon
        tech_list: List[str] = []
        tech_match = re.search(r"[\(\[](?:tech(?:nologies)?|tools?)?:?\s*([^\)\]]+)[\)\]]", first_line, re.IGNORECASE)
        if tech_match:
            raw_tech = tech_match.group(1)
            tech_list = [t.strip() for t in re.split(r"[,/|;]", raw_tech) if t.strip()]

        project_name = re.sub(r"[\(\[].*?[\)\]]", "", first_line).strip(" |-—–:")
        url_match = URL_REGEX.search(block)
        url = url_match.group(0).strip() if url_match else None

        desc_lines = lines[1:] if len(lines) > 1 else []
        description = "\n".join(desc_lines) if desc_lines else None

        projects.append({
            "project_name": project_name or "Technical Project",
            "role": None,
            "description": description,
            "technologies_used": tech_list if tech_list else None,
            "url": url,
            "start_date": None,
            "end_date": None,
        })

    return projects


def extract_structured_certifications(cert_text: str) -> List[Dict[str, Any]]:
    """Extracts certification titles and organizations from the CERTIFICATIONS section."""
    if not cert_text or not cert_text.strip():
        return []

    certs: List[Dict[str, Any]] = []
    lines = [l.strip().lstrip("•-* ") for l in cert_text.split("\n") if l.strip()]

    for line in lines:
        if len(line) < 3:
            continue
        org = None
        name = line
        if " - " in line:
            parts = line.split(" - ", 1)
            name, org = parts[0].strip(), parts[1].strip()
        elif " by " in line.lower():
            parts = re.split(r"\s+by\s+", line, flags=re.IGNORECASE)
            name, org = parts[0].strip(), parts[1].strip()

        certs.append({
            "name": name,
            "issuing_organization": org,
            "issue_date": None,
            "expiration_date": None,
            "credential_id": None,
            "credential_url": None,
        })

    return certs
