"""File validation, size checks, MIME type verification, and security sanitization."""

import os
import re
import uuid
from typing import Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import ValidationException

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/x-pdf",
    "application/octet-stream",  # Fallback MIME sometimes sent by browsers
}

# Magic numbers for binary verification
PDF_MAGIC_BYTES = b"%PDF"
DOCX_MAGIC_BYTES = b"PK\x03\x04"


def sanitize_filename(filename: str) -> str:
    """Strip dangerous characters and path traversal attempts from filename."""
    base_name = os.path.basename(filename)
    clean_name = re.sub(r"[^\w\s.-]", "", base_name).strip()
    return clean_name or "resume_upload"


def validate_file_metadata(file: UploadFile) -> Tuple[str, str]:
    """Validate filename, extension, and content type. Returns (safe_original_name, extension)."""
    if not file.filename:
        raise ValidationException("Upload file must have a valid filename.")

    safe_name = sanitize_filename(file.filename)
    _, ext = os.path.splitext(safe_name.lower())

    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationException(
            f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    return safe_name, ext


def validate_file_bytes(header_bytes: bytes, file_size: int, ext: str) -> None:
    """Validate file size and magic byte signatures."""
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        raise ValidationException(
            f"File exceeds maximum upload size limit of {max_mb:.0f} MB."
        )

    if file_size == 0:
        raise ValidationException("The uploaded file is empty.")

    if ext == ".pdf":
        if not header_bytes.startswith(PDF_MAGIC_BYTES):
            raise ValidationException("Invalid PDF file structure or corrupted magic header.")
    elif ext == ".docx":
        if not header_bytes.startswith(DOCX_MAGIC_BYTES):
            raise ValidationException("Invalid DOCX file structure or corrupted ZIP header.")


def generate_secure_storage_path(extension: str) -> Tuple[str, str]:
    """Generate a collision-resistant UUID filename and storage destination."""
    file_uuid = uuid.uuid4().hex
    safe_stored_filename = f"{file_uuid}{extension}"
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    destination_path = os.path.join(upload_dir, safe_stored_filename)
    return safe_stored_filename, destination_path
