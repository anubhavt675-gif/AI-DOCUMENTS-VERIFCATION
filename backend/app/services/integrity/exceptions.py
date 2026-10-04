"""
Custom Exceptions for Integrity Workflow.
"""


class IntegrityException(Exception):
    """Base exception for integrity operations."""
    pass


class IncompleteProcessingError(IntegrityException):
    """Raised when registration is attempted before document preprocessing and feature extraction are complete."""
    pass


class VerificationProcessingError(IntegrityException):
    """Raised when an unexpected error occurs during verification execution."""
    pass
