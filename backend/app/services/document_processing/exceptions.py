"""
Exceptions for document processing pipeline.
"""

class ProcessingError(Exception):
    """Base exception for all document processing pipeline errors."""
    pass


class UnsupportedFormatError(ProcessingError):
    """Raised when an uploaded document format is not supported."""
    pass


class CorruptedDocumentError(ProcessingError):
    """Raised when a document is corrupted, truncated, or unreadable."""
    pass


class PasswordProtectedError(ProcessingError):
    """Raised when a document is password protected or encrypted."""
    pass


class EmptyDocumentError(ProcessingError):
    """Raised when a document has 0 pages, 0 dimensions, or empty payload."""
    pass


class ExtractionError(ProcessingError):
    """Raised when an unrecoverable error occurs during text or metadata extraction."""
    pass
