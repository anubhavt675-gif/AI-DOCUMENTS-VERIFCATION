"""
Pydantic Schemas for IPFS Operations (Phase 7).
"""
from typing import Optional
from pydantic import BaseModel, Field


class IPFSUploadResponse(BaseModel):
    success: bool = True
    document_id: str
    ipfs_cid: str
    status: str = "stored"
    content_size_bytes: int
    content_sha256: str
    storage_provider: str


class IPFSRetrievalResponse(BaseModel):
    document_id: str
    ipfs_cid: str
    content_size_bytes: int
    content_sha256: str
    retrieval_status: str = "success"


class IPFSVerifyResponse(BaseModel):
    document_id: str
    ipfs_cid: str
    current_file_sha256: Optional[str] = None
    retrieved_content_sha256: Optional[str] = None
    hash_match: bool
    retrieval_success: bool
    status: str = Field(
        ...,
        description="VERIFIED, HASH_MISMATCH, RETRIEVAL_FAILED, or CID_NOT_FOUND",
    )
