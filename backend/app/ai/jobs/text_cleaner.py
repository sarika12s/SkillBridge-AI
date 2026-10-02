"""Text cleaning and normalization for job descriptions preserving tech symbols."""

import re


def normalize_job_text(raw_text: str) -> str:
    """
    Cleans extraction artifacts, repeated punctuation, and formatting noise
    while preserving paragraphs, bullet points, and technology identifiers
    like C++, C#, .NET, Node.js, and React.js.
    """
    if not raw_text or not raw_text.strip():
        return ""

    text = raw_text

    # 1. Remove non-printable control characters except standard whitespace
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", text)

    # 2. Standardize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Standardize bullet symbols
    bullet_pattern = r"(?:^|\n)\s*[•\*\-\–\—▪▫◦✦➢]\s*"
    text = re.sub(bullet_pattern, "\n• ", text)

    # 4. Standardize horizontal whitespace (tabs and repeated spaces) without collapsing newlines
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
        cleaned_lines.append(cleaned_line)

    text = "\n".join(cleaned_lines)

    # 5. Collapse excessive blank lines (more than 2 consecutive newlines to 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
