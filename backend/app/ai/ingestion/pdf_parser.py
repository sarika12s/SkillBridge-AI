"""PDF parsing module using PyMuPDF with automatic OCR fallback."""

import re
from typing import Tuple, Dict, Any
import fitz  # PyMuPDF
from app.core.exceptions import ValidationException
from app.ai.ingestion.text_quality import evaluate_text_quality, TextQualityStatus
from app.ai.ingestion.ocr_engine import extract_text_via_ocr


def clean_extracted_text(text: str) -> str:
    """Normalize whitespace, remove null bytes, and standardize line endings."""
    if not text:
        return ""
    # Remove null bytes
    cleaned = text.replace("\x00", "")
    # Normalize Windows CRLF and CR to LF
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-breaking spaces with standard space
    cleaned = cleaned.replace("\xa0", " ")
    # Collapse 3 or more consecutive newlines into 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    # Remove excessive horizontal spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


def parse_pdf_document(pdf_path: str) -> Tuple[str, int, int, str, Dict[str, Any]]:
    """
    Parses a PDF document, evaluates text sufficiency, and triggers OCR fallback if required.
    
    Returns:
        (cleaned_text, page_count, character_count, extraction_method, quality_metrics)
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise ValidationException(f"Unable to read PDF file. File may be corrupted: {str(e)}")

    if doc.is_encrypted or doc.needs_pass:
        doc.close()
        raise ValidationException(
            "The uploaded PDF is password-protected. Please remove the password and re-upload."
        )

    page_count = len(doc)
    if page_count == 0:
        doc.close()
        raise ValidationException("The uploaded PDF contains no pages.")

    raw_pages = []
    try:
        for page_idx in range(page_count):
            page = doc.load_page(page_idx)
            page_text = page.get_text("text")
            if page_text and page_text.strip():
                raw_pages.append(page_text.strip())
    finally:
        doc.close()

    direct_text = "\n\n".join(raw_pages)
    cleaned_direct_text = clean_extracted_text(direct_text)

    # Evaluate quality of direct text extraction
    quality_status, metrics = evaluate_text_quality(cleaned_direct_text, is_pdf=True)

    if quality_status == TextQualityStatus.GOOD_TEXT:
        return (
            cleaned_direct_text,
            page_count,
            len(cleaned_direct_text),
            "TEXT",
            metrics,
        )

    # Trigger OCR fallback when direct text extraction is insufficient or document is scanned
    ocr_text, _ = extract_text_via_ocr(pdf_path)
    cleaned_ocr_text = clean_extracted_text(ocr_text)

    ocr_quality_status, ocr_metrics = evaluate_text_quality(cleaned_ocr_text, is_pdf=False)
    if ocr_quality_status == TextQualityStatus.EXTRACTION_FAILED:
        raise ValidationException(
            "Document parsing failed: Neither direct text extraction nor OCR could extract "
            "sufficient readable text from this PDF."
        )

    return (
        cleaned_ocr_text,
        page_count,
        len(cleaned_ocr_text),
        "OCR",
        ocr_metrics,
    )
