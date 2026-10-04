"""
Pydantic Schemas for Hyperledger Fabric Blockchain Operations (Phase 6).
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BlockchainRegisterRequest(BaseModel):
    issuer_reference: Optional[str] = "Official Document Authority"
    document_version: Optional[str] = "1.0"


class BlockchainRegisterResponse(BaseModel):
    success: bool = True
    document_id: str
    blockchain_status: str = "registered"
    transaction_id: str
    document_hash: str
    ipfs_cid: str
    channel_name: str
    chaincode_name: str
    block_reference: Optional[str] = None
    registered_at: str


class BlockchainVerifyResponse(BaseModel):
    document_id: str
    current_hash: Optional[str] = None
    registered_hash: Optional[str] = None
    hash_match: bool
    ipfs_cid_match: bool
    blockchain_record_found: bool
    integrity_status: str = Field(
        ...,
        description="MATCH, HASH_MISMATCH, RECORD_NOT_FOUND, IPFS_REFERENCE_MISMATCH, or VERIFICATION_ERROR",
    )
    transaction_id: Optional[str] = None
    registered_at: Optional[str] = None


class BlockchainHistoryEntry(BaseModel):
    transaction_id: str
    timestamp: str
    document_version: str
    document_hash: str
    ipfs_cid: str
    event_type: str
    block_number: Optional[int] = None


class BlockchainHistoryResponse(BaseModel):
    document_id: str
    total_events: int
    history: List[BlockchainHistoryEntry]
