"""
Document processing and ingestion module.
"""
from app.services.document_processing.exceptions import (
    CorruptedDocumentError,
    EmptyDocumentError,
    ExtractionError,
    PasswordProtectedError,
    ProcessingError,
    UnsupportedFormatError,
)
from app.services.document_processing.models import (
    DocumentFingerprint,
    OCRResult,
    ProcessingResult,
    StandardizedMetadata,
    TextExtractionResult,
)
from app.services.document_processing.processor import (
    calculate_sha256,
    process_document,
)

__all__ = [
    "calculate_sha256",
    "process_document",
    "ProcessingError",
    "UnsupportedFormatError",
    "CorruptedDocumentError",
    "PasswordProtectedError",
    "EmptyDocumentError",
    "ExtractionError",
    "StandardizedMetadata",
    "OCRResult",
    "DocumentFingerprint",
    "TextExtractionResult",
    "ProcessingResult",
]
