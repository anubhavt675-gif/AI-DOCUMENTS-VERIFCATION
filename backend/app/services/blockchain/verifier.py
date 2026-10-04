"""
Blockchain Verification Service (Phase 6).
Compares current file SHA-256 and IPFS reference against the immutable on-chain record.
Produces objective technical integrity statuses:
- MATCH
- HASH_MISMATCH
- RECORD_NOT_FOUND
- IPFS_REFERENCE_MISMATCH
- VERIFICATION_ERROR
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.blockchain.fabric_client import FabricClient
from app.services.blockchain.schemas import BlockchainVerifyResponse

logger = logging.getLogger(__name__)


class BlockchainVerifier:
    """Verifies document technical integrity against Hyperledger Fabric records."""

    def __init__(self, fabric_client: Optional[FabricClient] = None):
        self.fabric_client = fabric_client or FabricClient()

    def verify_document(
        self,
        db: Session,
        document_id: str,
    ) -> BlockchainVerifyResponse:
        """
        Executes blockchain hash and IPFS reference verification.
        """
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            return BlockchainVerifyResponse(
                document_id=document_id,
                current_hash=None,
                registered_hash=None,
                hash_match=False,
                ipfs_cid_match=False,
                blockchain_record_found=False,
                integrity_status="RECORD_NOT_FOUND",
            )

        # Compute current file hash
        current_hash = None
        if doc.file_path and Path(doc.file_path).exists():
            try:
                with open(doc.file_path, "rb") as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                current_hash = doc.current_sha256 or doc.file_hash
        else:
            current_hash = doc.current_sha256 or doc.file_hash

        # 1. Fetch blockchain record
        try:
            onchain_record = self.fabric_client.get_document(document_id)
            registered_hash = onchain_record.get("document_hash")
            registered_cid = onchain_record.get("ipfs_cid")
            tx_id = onchain_record.get("tx_id")
            registered_at = onchain_record.get("registered_at")
        except Exception as e:
            logger.info(f"No blockchain record found for {document_id}: {e}")
            return BlockchainVerifyResponse(
                document_id=document_id,
                current_hash=current_hash,
                registered_hash=None,
                hash_match=False,
                ipfs_cid_match=False,
                blockchain_record_found=False,
                integrity_status="RECORD_NOT_FOUND",
            )

        # 3. Compare hash and IPFS reference
        hash_match = bool(current_hash and registered_hash and current_hash.lower() == registered_hash.lower())
        ipfs_cid_match = bool(doc.current_ipfs_cid and registered_cid and doc.current_ipfs_cid == registered_cid)

        if not hash_match:
            integrity_status = "HASH_MISMATCH"
        elif not ipfs_cid_match:
            integrity_status = "IPFS_REFERENCE_MISMATCH"
        else:
            integrity_status = "MATCH"

        return BlockchainVerifyResponse(
            document_id=document_id,
            current_hash=current_hash,
            registered_hash=registered_hash,
            hash_match=hash_match,
            ipfs_cid_match=ipfs_cid_match,
            blockchain_record_found=True,
            integrity_status=integrity_status,
            transaction_id=tx_id,
            registered_at=registered_at,
        )
