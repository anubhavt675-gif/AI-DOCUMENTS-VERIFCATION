"""
Data models for document processing pipeline results.
"""
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StandardizedMetadata:
    """
    Standardized document metadata schema across all formats (PDF, DOCX, Images).
    """
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    keywords: Optional[str] = None
    created_at: Optional[str] = None      # ISO 8601 string
    modified_at: Optional[str] = None     # ISO 8601 string
    last_modified_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OCRResult:
    """
    OCR extraction details.
    """
    used: bool = False
    status: str = "not_required"  # "not_required", "completed", "unavailable", "failed"
    extracted_text: str = ""
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentFingerprint:
    """
    Cryptographic fingerprint of original uploaded file.
    """
    algorithm: str = "SHA-256"
    hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TextExtractionResult:
    """
    Extracted text statistics and contents.
    """
    raw_text: str = ""
    cleaned_text: str = ""
    word_count: int = 0
    character_count: int = 0
    paragraph_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessingResult:
    """
    Complete standardized result of the document preprocessing pipeline.
    """
    document_id: str
    file_type: str
    fingerprint: DocumentFingerprint
    text: TextExtractionResult
    metadata: StandardizedMetadata
    structure: Dict[str, Any] = field(default_factory=dict)
    ocr: OCRResult = field(default_factory=OCRResult)
    page_count: int = 1
    image_count: int = 0
    table_count: int = 0
    paragraph_count: int = 0
    processing_error: Optional[str] = None
