"""
Base interface for document format processors.
"""
from abc import ABC, abstractmethod
from pathlib import Path

from app.services.document_processing.models import DocumentFingerprint, ProcessingResult


class BaseDocumentProcessor(ABC):
    """
    Abstract base class for all format-specific document processors.
    """

    @abstractmethod
    def process(
        self,
        file_path: Path,
        original_filename: str,
        document_id: str,
        fingerprint: DocumentFingerprint,
    ) -> ProcessingResult:
        """
        Process the document file and return a standardized ProcessingResult.
        Must not mutate or overwrite the original file.
        """
        pass
