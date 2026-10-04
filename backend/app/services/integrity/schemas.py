"""
Pydantic Schemas for Unified Integrity Verification and Registration (Phases 5-7).
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MLSignal(BaseModel):
    model: str = "Autoencoder"
    model_version: str
    reconstruction_error: Optional[float] = None
    anomaly_score: float
    prediction: int = Field(..., description="0 = NORMAL, 1 = ANOMALOUS")
    status: str = Field(..., description="NORMAL or ANOMALOUS")


class IPFSSignal(BaseModel):
    cid: Optional[str] = None
    hash_match: bool
    retrieval_success: bool
    status: str


class BlockchainSignal(BaseModel):
    record_found: bool
    hash_match: bool
    transaction_id: Optional[str] = None
    registered_at: Optional[str] = None
    status: str


class IntegritySignal(BaseModel):
    status: str = Field(..., description="MATCH, HASH_MISMATCH, RECORD_NOT_FOUND, or UNREGISTERED")


class IntegratedVerificationResponse(BaseModel):
    document_id: str
    ml: MLSignal
    ipfs: IPFSSignal
    blockchain: BlockchainSignal
    integrity: IntegritySignal
    final_status: str = Field(
        ...,
        description="VERIFIED_INTEGRITY, INTEGRITY_MISMATCH, ANOMALY_DETECTED, UNREGISTERED, or VERIFICATION_ERROR",
    )
    technical_explanation: str
    verification_id: Optional[str] = None
    verified_at: str


class IntegratedRegistrationResponse(BaseModel):
    success: bool = True
    document_id: str
    preprocessing_status: str
    features_generated: bool
    ipfs_cid: str
    document_hash: str
    blockchain_tx_id: str
    final_status: str
    registered_at: str
