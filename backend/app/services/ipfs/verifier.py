"""
IPFS Content Verification Service (Phase 7).
Verifies that IPFS content exactly matches the registered cryptographic SHA-256 fingerprint.
Reports technical statuses:
- VERIFIED
- HASH_MISMATCH
- RETRIEVAL_FAILED
- CID_NOT_FOUND
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.ipfs.client import IPFSClient
from app.services.ipfs.schemas import IPFSVerifyResponse

logger = logging.getLogger(__name__)


class IPFSVerifier:
    """Verifies technical integrity of content stored on IPFS."""

    def __init__(self, client: Optional[IPFSClient] = None):
        self.client = client or IPFSClient()

    def verify_document_ipfs(
        self,
        db: Session,
        document_id: str,
    ) -> IPFSVerifyResponse:
        """
        Validates IPFS content integrity against the registered document hash.
        """
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            return IPFSVerifyResponse(
                document_id=document_id,
                ipfs_cid="",
                current_file_sha256=None,
                retrieved_content_sha256=None,
                hash_match=False,
                retrieval_success=False,
                status="CID_NOT_FOUND",
            )

        cid = doc.current_ipfs_cid
        if not cid:
            return IPFSVerifyResponse(
                document_id=document_id,
                ipfs_cid="",
                current_file_sha256=getattr(doc, "current_sha256", None) or getattr(doc, "file_hash", None),
                retrieved_content_sha256=None,
                hash_match=False,
                retrieval_success=False,
                status="CID_NOT_FOUND",
            )

        # 1. Calculate current local file hash
        file_sha256 = None
        if doc.file_path and Path(doc.file_path).exists():
            with open(doc.file_path, "rb") as f:
                file_sha256 = hashlib.sha256(f.read()).hexdigest()

        # 2. Retrieve content from IPFS
        try:
            content = self.client.get_bytes(cid)
            ipfs_sha256 = hashlib.sha256(content).hexdigest()
            retrieval_success = True
        except Exception as e:
            logger.warning(f"Failed to retrieve IPFS content for doc {document_id}: {e}")
            return IPFSVerifyResponse(
                document_id=document_id,
                ipfs_cid=cid,
                current_file_sha256=file_sha256,
                retrieved_content_sha256=None,
                hash_match=False,
                retrieval_success=False,
                status="RETRIEVAL_FAILED",
            )

        # 3. Compare hashes
        reference_hash = file_sha256 or getattr(doc, "current_sha256", None) or getattr(doc, "file_hash", None)
        hash_match = bool(reference_hash and ipfs_sha256 == reference_hash)
        status = "VERIFIED" if hash_match else "HASH_MISMATCH"

        return IPFSVerifyResponse(
            document_id=document_id,
            ipfs_cid=cid,
            current_file_sha256=reference_hash,
            retrieved_content_sha256=ipfs_sha256,
            hash_match=hash_match,
            retrieval_success=retrieval_success,
            status=status,
        )
