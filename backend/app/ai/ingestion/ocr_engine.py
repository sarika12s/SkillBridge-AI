"""OCR engine utilizing PyMuPDF pixmap rendering and Tesseract OCR fallback."""

import io
import logging
from typing import Tuple, List
import fitz  # PyMuPDF
from PIL import Image, ImageOps
import pytesseract
from app.core.exceptions import ValidationException

logger = logging.getLogger(__name__)


def extract_text_via_ocr(pdf_path: str, max_pages: int = 5) -> Tuple[str, int]:
    """
    Renders PDF pages to high-resolution bitmaps and extracts text using Tesseract OCR.
    
    Returns:
        (extracted_ocr_text, page_count)
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise ValidationException(f"Failed to open PDF for OCR: {str(e)}")

    page_count = len(doc)
    extracted_pages: List[str] = []

    # Limit to reasonable page count to avoid resource exhaustion
    pages_to_process = min(page_count, max_pages)

    try:
        for page_num in range(pages_to_process):
            page = doc.load_page(page_num)
            
            # Render at 300 DPI for optimal OCR readability
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))

            # Image Preprocessing: Grayscale and autocontrast
            gray_image = ImageOps.grayscale(image)
            enhanced_image = ImageOps.autocontrast(gray_image)

            # Execute Tesseract OCR
            page_text = pytesseract.image_to_string(
                enhanced_image, config="--psm 3 -l eng"
            )
            if page_text and page_text.strip():
                extracted_pages.append(page_text.strip())

        full_ocr_text = "\n\n".join(extracted_pages)
        return full_ocr_text, page_count

    except pytesseract.TesseractNotFoundError:
        logger.warning("Tesseract OCR executable not found on host system PATH.")
        raise ValidationException(
            "The uploaded document is a scanned image, but the OCR service (Tesseract) "
            "is not currently installed or configured on the server. Please upload a text-based PDF or DOCX."
        )
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        raise ValidationException(f"OCR processing failed on scanned document: {str(e)}")
    finally:
        doc.close()
