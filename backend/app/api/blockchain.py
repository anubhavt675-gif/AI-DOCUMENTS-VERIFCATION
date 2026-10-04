"""
Blockchain API Router (Phase 6).
Provides endpoints for registering document fingerprints on Hyperledger Fabric,
verifying technical cryptographic hash matches, and querying immutable audit history.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.blockchain import (
    BlockchainRegisterRequest,
    BlockchainRegisterResponse,
    BlockchainVerifyResponse,
    BlockchainHistoryResponse,
    BlockchainHistoryEntry,
    DocumentRegistry,
    BlockchainVerifier,
    FabricClient,
)

router = APIRouter(prefix="/api/blockchain", tags=["Hyperledger Fabric Blockchain"])

registry = DocumentRegistry()
verifier = BlockchainVerifier()
fabric_client = FabricClient()


@router.post("/register/{document_id}", response_model=BlockchainRegisterResponse)
def register_on_blockchain(
    document_id: str,
    payload: BlockchainRegisterRequest = BlockchainRegisterRequest(),
    db: Session = Depends(get_db),
):
    """
    Submits document SHA-256 fingerprint and IPFS CID to Hyperledger Fabric.
    Returns real cryptographic transaction identifier.
    """
    try:
        return registry.register_document(
            db=db,
            document_id=document_id,
            issuer_reference=payload.issuer_reference or "Official Government Authority",
            document_version=payload.document_version or "1.0",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Blockchain registration failed: {str(e)}",
        )


@router.get("/verify/{document_id}", response_model=BlockchainVerifyResponse)
def verify_blockchain_fingerprint(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Compares current file SHA-256 and IPFS reference against on-chain record.
    Returns objective technical integrity status: MATCH, HASH_MISMATCH, RECORD_NOT_FOUND, etc.
    """
    try:
        return verifier.verify_document(db, document_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Blockchain verification failed: {str(e)}",
        )


@router.get("/history/{document_id}", response_model=BlockchainHistoryResponse)
def get_blockchain_history(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves full immutable blockchain audit trail for a document from the ledger.
    """
    try:
        history_raw = fabric_client.get_document_history(document_id)
        entries = [
            BlockchainHistoryEntry(
                transaction_id=h["transaction_id"],
                timestamp=h["timestamp"],
                document_version=h.get("document_version", "1.0"),
                document_hash=h.get("document_hash", ""),
                ipfs_cid=h.get("ipfs_cid", ""),
                event_type=h.get("event_type", "REGISTERED"),
                block_number=h.get("block_number"),
            )
            for h in history_raw
        ]
        return BlockchainHistoryResponse(
            document_id=document_id,
            total_events=len(entries),
            history=entries,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch blockchain history: {str(e)}",
        )
