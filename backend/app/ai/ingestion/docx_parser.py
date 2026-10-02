"""DOCX parsing module using python-docx to extract paragraphs, headings, and tables."""

from typing import Tuple, Dict, Any, List
import docx
from app.core.exceptions import ValidationException
from app.ai.ingestion.pdf_parser import clean_extracted_text
from app.ai.ingestion.text_quality import evaluate_text_quality, TextQualityStatus


def parse_docx_document(docx_path: str) -> Tuple[str, int, int, str, Dict[str, Any]]:
    """
    Parses a DOCX document extracting paragraphs, headings, and tables in logical sequence.
    
    Returns:
        (cleaned_text, page_count, character_count, extraction_method, quality_metrics)
    """
    try:
        doc = docx.Document(docx_path)
    except Exception as e:
        raise ValidationException(f"Unable to read DOCX file. File may be corrupted or invalid: {str(e)}")

    extracted_blocks: List[str] = []

    # 1. Iterate through paragraphs
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            extracted_blocks.append(text)

    # 2. Iterate through tables (common in resumes for skills, education, experience)
    for table in doc.tables:
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_cells:
                # Deduplicate identical adjacent cells caused by merged table cells
                deduped = []
                for cell in row_cells:
                    if not deduped or deduped[-1] != cell:
                        deduped.append(cell)
                extracted_blocks.append(" | ".join(deduped))

    full_text = "\n\n".join(extracted_blocks)
    cleaned_text = clean_extracted_text(full_text)

    # Evaluate quality of extracted DOCX text
    quality_status, metrics = evaluate_text_quality(cleaned_text, is_pdf=False)

    if quality_status == TextQualityStatus.EXTRACTION_FAILED:
        raise ValidationException(
            f"The uploaded DOCX document contains insufficient text to parse as a resume: {metrics['reason']}"
        )

    return (
        cleaned_text,
        1,  # DOCX files do not have explicit pagination metadata in XML
        len(cleaned_text),
        "TEXT",
        metrics,
    )
