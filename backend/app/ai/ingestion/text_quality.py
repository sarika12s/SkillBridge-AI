"""Deterministic text quality evaluator to determine if direct extraction is sufficient or OCR is required."""

import re
from typing import Dict, Any, Tuple
from enum import Enum


class TextQualityStatus(str, Enum):
    GOOD_TEXT = "GOOD_TEXT"
    OCR_REQUIRED = "OCR_REQUIRED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


# Configurable quality evaluation thresholds
# Rationale:
# - Standard 1-page resumes contain ~1,500 to 3,500 characters and 200+ words.
# - If character count is < 100 or meaningful words < 20, direct text extraction
#   is likely degraded (e.g. scanned PDF with only a small footer or watermark).
# - If alphabetic character ratio is < 50%, extraction likely produced binary glyph noise.
MIN_TEXT_CHARS = 100
MIN_MEANINGFUL_WORDS = 20
MIN_ALPHA_RATIO = 0.50
MAX_WHITESPACE_RATIO = 0.50


def evaluate_text_quality(
    raw_text: str, is_pdf: bool = True
) -> Tuple[TextQualityStatus, Dict[str, Any]]:
    """
    Evaluates extracted resume text using deterministic lexical and statistical criteria.
    
    Returns:
        (TextQualityStatus, metrics_dict)
    """
    if not raw_text or not raw_text.strip():
        if is_pdf:
            return TextQualityStatus.OCR_REQUIRED, {
                "character_count": 0,
                "word_count": 0,
                "alpha_ratio": 0.0,
                "reason": "Text stream is empty.",
            }
        return TextQualityStatus.EXTRACTION_FAILED, {
            "character_count": 0,
            "word_count": 0,
            "alpha_ratio": 0.0,
            "reason": "Document text is completely empty.",
        }

    total_chars = len(raw_text)
    words = re.findall(r"\b[A-Za-z]{2,}\b", raw_text)
    word_count = len(words)
    alpha_chars = sum(1 for c in raw_text if c.isalpha())
    whitespace_chars = sum(1 for c in raw_text if c.isspace())

    alpha_ratio = alpha_chars / total_chars if total_chars > 0 else 0.0
    whitespace_ratio = whitespace_chars / total_chars if total_chars > 0 else 0.0

    metrics = {
        "character_count": total_chars,
        "word_count": word_count,
        "alpha_ratio": round(alpha_ratio, 3),
        "whitespace_ratio": round(whitespace_ratio, 3),
    }

    # Evaluate sufficiency
    if total_chars < MIN_TEXT_CHARS or word_count < MIN_MEANINGFUL_WORDS:
        if is_pdf:
            metrics["reason"] = (
                f"Extracted characters ({total_chars} < {MIN_TEXT_CHARS}) or words "
                f"({word_count} < {MIN_MEANINGFUL_WORDS}) below threshold. Scanned image suspected."
            )
            return TextQualityStatus.OCR_REQUIRED, metrics
        else:
            metrics["reason"] = "Extracted text content below minimum threshold for a valid resume."
            return TextQualityStatus.EXTRACTION_FAILED, metrics

    if alpha_ratio < MIN_ALPHA_RATIO:
        if is_pdf:
            metrics["reason"] = f"Alphabetic character ratio ({alpha_ratio:.2f}) below threshold ({MIN_ALPHA_RATIO})."
            return TextQualityStatus.OCR_REQUIRED, metrics
        else:
            metrics["reason"] = "Extracted text has excessively high ratio of non-alphabetic glyphs/artifacts."
            return TextQualityStatus.EXTRACTION_FAILED, metrics

    metrics["reason"] = "Text density and lexical structure meet quality requirements."
    return TextQualityStatus.GOOD_TEXT, metrics
