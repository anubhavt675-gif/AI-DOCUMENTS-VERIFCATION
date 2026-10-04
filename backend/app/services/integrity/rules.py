"""
Decision Rules and Technical Status Mappings (Part D).
Guarantees objective, evidence-based reporting without false claims of real-world authenticity.
"""
from typing import Tuple

# Standardized Technical Statuses
STATUS_UNREGISTERED = "UNREGISTERED"
STATUS_VERIFIED_INTEGRITY = "VERIFIED_INTEGRITY"
STATUS_ANOMALY_DETECTED = "ANOMALY_DETECTED"
STATUS_INTEGRITY_MISMATCH = "INTEGRITY_MISMATCH"
STATUS_VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
STATUS_VERIFICATION_ERROR = "VERIFICATION_ERROR"


def determine_final_status(
    blockchain_found: bool,
    blockchain_hash_match: bool,
    ipfs_retrieval_success: bool,
    ipfs_hash_match: bool,
    ml_prediction: int,  # 0 = normal, 1 = anomalous
) -> Tuple[str, str]:
    """
    Evaluates separate technical signals and derives an objective technical status.
    Returns:
        Tuple of (status_string, explanation_text)
    """
    if not blockchain_found:
        return (
            STATUS_UNREGISTERED,
            "Document fingerprint has not been registered on the Hyperledger Fabric ledger.",
        )

    if not blockchain_hash_match:
        return (
            STATUS_INTEGRITY_MISMATCH,
            "Technical integrity mismatch detected: Current document SHA-256 fingerprint does not match the immutable on-chain record.",
        )

    if not ipfs_retrieval_success or not ipfs_hash_match:
        return (
            STATUS_INTEGRITY_MISMATCH,
            "Storage integrity mismatch detected: Content retrieved from IPFS does not match the registered technical fingerprint.",
        )

    if ml_prediction == 1:
        return (
            STATUS_ANOMALY_DETECTED,
            "Statistical anomaly detected: Cryptographic fingerprint matches on-chain record, but ML model flagged structural or content pattern deviations from baseline training distribution.",
        )

    return (
        STATUS_VERIFIED_INTEGRITY,
        "Technical integrity verified: Document SHA-256 matches immutable blockchain record, IPFS off-chain storage is consistent, and ML statistical model detected no pattern anomalies. Notice: Technical integrity establishes fingerprint consistency; it does not independently prove real-world issuer legitimacy.",
    )
