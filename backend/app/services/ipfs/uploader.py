"""
IPFS Document Uploader Service (Phase 7).
Handles file reading, SHA-256 computation, IPFS persistence, and database updating.
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.ipfs.client import IPFSClient
from app.services.ipfs.exceptions import IPFSUploadError
from app.services.ipfs.schemas import IPFSUploadResponse

logger = logging.getLogger(__name__)


class IPFSUploader:
    """Handles off-chain IPFS uploads for stored documents."""

    def __init__(self, client: Optional[IPFSClient] = None):
        self.client = client or IPFSClient()

    def upload_document(
        self,
        db: Session,
        document_id: str,
    ) -> IPFSUploadResponse:
        """
        Reads original file for document_id, persists bytes to IPFS,
        and records the resulting CID in the database.
        """
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise IPFSUploadError(f"Document {document_id} not found in database.")

        file_path = Path(doc.file_path)
        if not file_path.exists():
            raise IPFSUploadError(f"Physical file for document {document_id} not found at {file_path}")

        try:
            with open(file_path, "rb") as f:
                content = f.read()
        except Exception as e:
            raise IPFSUploadError(f"Failed to read file from disk: {e}") from e

        content_sha256 = hashlib.sha256(content).hexdigest()
        cid, provider = self.client.add_bytes(content)

        # Update document record with latest integrity fingerprints
        doc.current_ipfs_cid = cid
        doc.current_sha256 = content_sha256
        db.commit()
        db.refresh(doc)

        logger.info(f"Document {document_id} uploaded to IPFS: CID={cid}")

        return IPFSUploadResponse(
            success=True,
            document_id=document_id,
            ipfs_cid=cid,
            status="stored",
            content_size_bytes=len(content),
            content_sha256=content_sha256,
            storage_provider=provider,
        )
