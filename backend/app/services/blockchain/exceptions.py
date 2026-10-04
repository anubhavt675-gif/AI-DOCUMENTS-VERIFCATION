"""
Custom Exceptions for Hyperledger Fabric Integration (Phase 6).
"""


class BlockchainException(Exception):
    """Base exception for all blockchain operations."""
    pass


class FabricConnectionError(BlockchainException):
    """Raised when Hyperledger Fabric peer or gateway is unreachable."""
    pass


class DuplicateRegistrationError(BlockchainException):
    """Raised when an attempt is made to register a document already on the ledger."""
    pass


class RecordNotFoundError(BlockchainException):
    """Raised when a document fingerprint record does not exist on the ledger."""
    pass


class FabricTransactionError(BlockchainException):
    """Raised when a blockchain transaction proposal or commit fails."""
    pass
