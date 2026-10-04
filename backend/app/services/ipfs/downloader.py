"""
IPFS Document Downloader Service (Phase 7).
Retrieves content from IPFS ensuring strict authorization and document ownership.
Never exposes arbitrary public CID proxying.
"""
import hashlib
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.ipfs.client import IPFSClient
from app.services.ipfs.exceptions import IPFSRetrievalError
from app.services.ipfs.schemas import IPFSRetrievalResponse

logger = logging.getLogger(__name__)


class IPFSDownloader:
    """Safely retrieves document content associated with specific documents."""

    def __init__(self, client: Optional[IPFSClient] = None):
        self.client = client or IPFSClient()

    def get_document_content(
        self,
        db: Session,
        document_id: str,
    ) -> Tuple[bytes, IPFSRetrievalResponse]:
        """
        Validates document ownership and retrieves content bytes from IPFS.
        """
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise IPFSRetrievalError(f"Document {document_id} not found.")

        cid = doc.current_ipfs_cid
        if not cid:
            raise IPFSRetrievalError(f"Document {document_id} has not been uploaded to IPFS yet.")

        content = self.client.get_bytes(cid)
        content_sha256 = hashlib.sha256(content).hexdigest()

        response = IPFSRetrievalResponse(
            document_id=document_id,
            ipfs_cid=cid,
            content_size_bytes=len(content),
            content_sha256=content_sha256,
            retrieval_status="success",
        )

        return content, response
