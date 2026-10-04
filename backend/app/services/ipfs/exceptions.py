"""
Custom Exceptions for IPFS Integration (Phase 7).
"""


class IPFSException(Exception):
    """Base exception for all IPFS operations."""
    pass


class IPFSConnectionError(IPFSException):
    """Raised when IPFS node or storage endpoint is unreachable."""
    pass


class IPFSUploadError(IPFSException):
    """Raised when document content fails to persist to IPFS."""
    pass


class IPFSRetrievalError(IPFSException):
    """Raised when content cannot be retrieved for a given CID."""
    pass


class IPFSVerificationError(IPFSException):
    """Raised when IPFS content integrity or hash verification fails."""
    pass
