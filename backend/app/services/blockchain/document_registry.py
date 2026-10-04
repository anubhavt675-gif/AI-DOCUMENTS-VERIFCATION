"""
Document Registration Service for Hyperledger Fabric (Phase 6).
Handles reading original document bytes, computing SHA-256, verifying IPFS CID existence,
submitting the blockchain transaction, and recording in the blockchain_records table.
"""
from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models.blockchain_record import BlockchainRecord
from app.models.document import Document
from app.services.blockchain.fabric_client import FabricClient
from app.services.blockchain.exceptions import BlockchainException
from app.services.blockchain.schemas import BlockchainRegisterResponse

logger = logging.getLogger(__name__)


class DocumentRegistry:
    """Manages document fingerprint registration on Hyperledger Fabric."""

    def __init__(self, fabric_client: Optional[FabricClient] = None):
        self.fabric_client = fabric_client or FabricClient()

    def register_document(
        self,
        db: Session,
        document_id: str,
        issuer_reference: str = "Official Government Authority",
        document_version: str = "1.0",
    ) -> BlockchainRegisterResponse:
        """
        Executes complete blockchain registration flow for a document.
        """
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise BlockchainException(f"Document {document_id} not found in database.")

        if not doc.current_ipfs_cid:
            raise BlockchainException(
                f"Document {document_id} must be stored on IPFS before registering on blockchain."
            )

        # 1. Read file and compute SHA-256
        file_path = Path(doc.file_path)
        if not file_path.exists():
            raise BlockchainException(f"Physical file for document {document_id} not found at {file_path}")

        with open(file_path, "rb") as f:
            content_bytes = f.read()
        document_hash = hashlib.sha256(content_bytes).hexdigest()

        # 2. Submit transaction to Fabric
        tx_result = self.fabric_client.register_document(
            document_id=document_id,
            document_hash=document_hash,
            ipfs_cid=doc.current_ipfs_cid,
            document_version=document_version,
            issuer_reference=issuer_reference,
            hash_algorithm="SHA-256",
        )

        tx_id = tx_result["tx_id"]
        block_ref = str(tx_result.get("block_number"))

        # 3. Store in blockchain_records table
        record = BlockchainRecord(
            document_id=document_id,
            blockchain_network=self.fabric_client.network_name,
            channel_name=self.fabric_client.channel_name,
            chaincode_name=self.fabric_client.chaincode_name,
            transaction_id=tx_id,
            document_hash=document_hash,
            hash_algorithm="SHA-256",
            ipfs_cid=doc.current_ipfs_cid,
            blockchain_status="registered",
            block_reference=block_ref,
        )
        db.add(record)

        # Update document integrity status
        doc.integrity_status = "REGISTERED"
        doc.current_sha256 = document_hash
        db.commit()
        db.refresh(record)

        logger.info(f"Registered document {document_id} on blockchain Tx {tx_id}")

        return BlockchainRegisterResponse(
            success=True,
            document_id=document_id,
            blockchain_status="registered",
            transaction_id=tx_id,
            document_hash=document_hash,
            ipfs_cid=doc.current_ipfs_cid,
            channel_name=self.fabric_client.channel_name,
            chaincode_name=self.fabric_client.chaincode_name,
            block_reference=block_ref,
            registered_at=tx_result["registered_at"],
        )
