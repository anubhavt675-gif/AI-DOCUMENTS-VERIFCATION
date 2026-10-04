"""
Main Document Preprocessing Orchestrator.
Calculates SHA-256 fingerprint from original file bytes, selects format processor,
and produces standardized ProcessingResult.
"""
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, Type

from app.services.document_processing.base_processor import BaseDocumentProcessor
from app.services.document_processing.docx_processor import DOCXProcessor
from app.services.document_processing.exceptions import (
    ProcessingError,
    UnsupportedFormatError,
)
from app.services.document_processing.image_processor import ImageProcessor
from app.services.document_processing.models import (
    DocumentFingerprint,
    ProcessingResult,
)
from app.services.document_processing.pdf_processor import PDFProcessor
from app.services.document_processing.text_processor import TextProcessor

logger = logging.getLogger("app.services.document_processing.orchestrator")


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 cryptographic hash of the original file bytes.
    Processes in 64 KB chunks to support arbitrarily large files with constant memory.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


class DocumentProcessorFactory:
    """
    Registry and factory for document format processors.
    Enables pluggable architecture for adding new formats easily.
    """

    def __init__(self):
        self._processors: Dict[str, Type[BaseDocumentProcessor]] = {}
        # Register default processors
        self.register([".pdf", "application/pdf"], PDFProcessor)
        self.register(
            [
                ".docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
            ],
            DOCXProcessor,
        )
        self.register(
            [
                ".jpg",
                ".jpeg",
                ".png",
                "image/jpeg",
                "image/jpg",
                "image/png",
            ],
            ImageProcessor,
        )
        self.register(
            [".txt", "text/plain"],
            TextProcessor,
        )

    def register(self, keys: list[str], processor_cls: Type[BaseDocumentProcessor]) -> None:
        """Register a processor class for extensions or mime types."""
        for key in keys:
            self._processors[key.lower()] = processor_cls

    def get_processor(
        self, file_path: Path, mime_type: Optional[str] = None
    ) -> BaseDocumentProcessor:
        """
        Select processor based on MIME type or file extension.
        """
        # Try MIME type match
        if mime_type and mime_type.lower() in self._processors:
            cls = self._processors[mime_type.lower()]
            logger.info(f"Selected processor '{cls.__name__}' by MIME type '{mime_type}'")
            return cls()

        # Try Extension match
        ext = file_path.suffix.lower()
        if ext in self._processors:
            cls = self._processors[ext]
            logger.info(f"Selected processor '{cls.__name__}' by extension '{ext}'")
            return cls()

        logger.error(f"No processor registered for file '{file_path.name}' (mime={mime_type}, ext={ext})")
        raise UnsupportedFormatError(
            f"Unsupported document format: ext='{ext}', mime='{mime_type}'. "
            "Supported formats: PDF, DOCX, JPEG, PNG."
        )


# Global factory instance
_factory = DocumentProcessorFactory()


def process_document(
    file_path: Path,
    original_filename: str,
    document_id: str,
    file_type: Optional[str] = None,
) -> ProcessingResult:
    """
    Main entry point for document ingestion and preprocessing pipeline.

    Workflow:
    1. Calculate SHA-256 fingerprint on original unmodified file bytes
    2. Identify and select format processor
    3. Run text & metadata extraction, structural analysis, and data normalization
    4. Return standardized ProcessingResult
    """
    logger.info(f"Processing document {document_id} ({original_filename}) at path {file_path}")

    # Step 1: Calculate SHA-256 fingerprint
    logger.info(f"Generating SHA-256 fingerprint for document {document_id}")
    file_hash = calculate_sha256(file_path)
    fingerprint = DocumentFingerprint(algorithm="SHA-256", hash=file_hash)
    logger.info(f"Generated SHA-256 for {document_id}: {file_hash[:16]}...")

    # Step 2: Select format processor
    processor = _factory.get_processor(file_path, file_type)

    # Step 3: Execute extraction pipeline
    result = processor.process(
        file_path=file_path,
        original_filename=original_filename,
        document_id=document_id,
        fingerprint=fingerprint,
    )

    logger.info(f"Completed processing pipeline for document {document_id}")
    return result
