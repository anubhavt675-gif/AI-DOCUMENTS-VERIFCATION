"""
IPFS Storage API Router (Phase 7).
Handles off-chain document storage, CID generation, content retrieval, and hash verification.
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.services.ipfs import IPFSUploader, IPFSDownloader, IPFSVerifier
from app.services.ipfs.schemas import (
    IPFSUploadResponse,
    IPFSRetrievalResponse,
    IPFSVerifyResponse,
)

router = APIRouter(prefix="/api/ipfs", tags=["IPFS Storage"])

uploader = IPFSUploader()
downloader = IPFSDownloader()
verifier = IPFSVerifier()


@router.post("/upload/{document_id}", response_model=IPFSUploadResponse)
def upload_to_ipfs(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Persists document bytes into IPFS, generates a real CID,
    and updates document metadata in the database.
    """
    try:
        return uploader.upload_document(db, document_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"IPFS upload failed: {str(e)}",
        )


@router.get("/{document_id}")
def retrieve_from_ipfs(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Safely retrieves document content from IPFS, strictly validating
    document ownership and CID mapping.
    """
    try:
        content_bytes, meta = downloader.get_document_content(db, document_id)
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        media_type = doc.mime_type if doc and doc.mime_type else "application/octet-stream"
        filename = doc.original_filename if doc else f"document_{document_id}"

        return Response(
            content=content_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "X-IPFS-CID": meta.ipfs_cid,
                "X-Content-SHA256": meta.content_sha256,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPFS retrieval failed: {str(e)}",
        )


@router.get("/verify/{document_id}", response_model=IPFSVerifyResponse)
def verify_ipfs_content(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Validates that content retrieved for the registered CID exactly matches
    the document's stored cryptographic SHA-256 fingerprint.
    """
    try:
        return verifier.verify_document_ipfs(db, document_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IPFS verification failed: {str(e)}",
        )
