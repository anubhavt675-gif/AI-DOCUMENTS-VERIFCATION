"""
Unified Integrity Workflow API Router (Part D).
Orchestrates multi-phase registration and comprehensive verification:
ML (Autoencoder) + IPFS (Off-chain storage) + Hyperledger Fabric (Immutable fingerprint) -> Technical Evidence.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.integrity_verification import IntegrityVerification
from app.services.integrity import (
    VerificationEngine,
    IntegratedRegistrationResponse,
    IntegratedVerificationResponse,
)

router = APIRouter(prefix="/api/documents", tags=["Unified Integrity Workflow"])

engine = VerificationEngine()


@router.post("/{document_id}/register-integrity", response_model=IntegratedRegistrationResponse)
def register_document_integrity(
    document_id: str,
    issuer_reference: str = "Official Government Authority",
    document_version: str = "1.0",
    db: Session = Depends(get_db),
):
    """
    Executes end-to-end integrity registration:
    1. Validates Phase 2 preprocessing & Phase 3 features
    2. Stores file bytes in IPFS and receives real CID
    3. Commits SHA-256 fingerprint + CID to Hyperledger Fabric
    4. Records transaction references and updates document status
    """
    try:
        return engine.register_integrity(
            db=db,
            document_id=document_id,
            issuer_reference=issuer_reference,
            document_version=document_version,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integrity registration failed: {str(e)}",
        )


@router.post("/{document_id}/verify-integrity", response_model=IntegratedVerificationResponse)
def verify_document_integrity(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Executes multi-signal technical verification:
    - ML Anomaly score & reconstruction error (Autoencoder)
    - IPFS off-chain storage retrieval & hash match
    - Hyperledger Fabric cryptographic on-chain hash match
    - Consolidates technical evidence into an objective integrity status
    """
    try:
        return engine.verify_integrity(db=db, document_id=document_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integrity verification failed: {str(e)}",
        )


@router.get("/{document_id}/integrity-history")
def get_integrity_verification_history(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns full chronological verification history for a document.
    """
    records = (
        db.query(IntegrityVerification)
        .filter(IntegrityVerification.document_id == document_id)
        .order_by(IntegrityVerification.verified_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "final_status": r.final_status,
            "hash_match": r.hash_match,
            "ipfs_match": r.ipfs_match,
            "blockchain_match": r.blockchain_match,
            "ipfs_cid": r.ipfs_cid,
            "current_hash": r.current_hash,
            "registered_hash": r.registered_hash,
            "details": r.verification_details_json,
            "verified_at": r.verified_at.isoformat() if r.verified_at else None,
        }
        for r in records
    ]
