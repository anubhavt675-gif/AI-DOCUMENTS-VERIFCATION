"""
Evidence Aggregation Engine (Part D).
Combines independent signals (ML anomaly score, IPFS content verification,
Hyperledger Fabric on-chain fingerprint) into a comprehensive evidence bundle.
Never collapses or hides individual signals.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.integrity_verification import IntegrityVerification
from app.services.integrity.rules import determine_final_status
from app.services.integrity.schemas import (
    IntegratedVerificationResponse,
    MLSignal,
    IPFSSignal,
    BlockchainSignal,
    IntegritySignal,
)

logger = logging.getLogger(__name__)


class EvidenceEngine:
    """Consolidates technical verification signals and persists audit records."""

    def compile_evidence(
        self,
        db: Session,
        document_id: str,
        ml_result: Dict[str, Any],
        ipfs_result: Dict[str, Any],
        blockchain_result: Dict[str, Any],
    ) -> IntegratedVerificationResponse:
        """
        Synthesizes technical evidence into a structured, tamper-evident verification record.
        """
        doc = db.query(Document).filter(Document.document_id == document_id).first()

        # Parse ML Signal
        ml_model = ml_result.get("model", "Autoencoder")
        ml_version = ml_result.get("model_version", "1.0.0")
        ml_rec_err = ml_result.get("reconstruction_error")
        ml_score = float(ml_result.get("anomaly_score", 0.0))
        ml_pred = int(ml_result.get("prediction", 0))
        ml_status = "ANOMALOUS" if ml_pred == 1 else "NORMAL"

        ml_signal = MLSignal(
            model=ml_model,
            model_version=ml_version,
            reconstruction_error=ml_rec_err,
            anomaly_score=ml_score,
            prediction=ml_pred,
            status=ml_status,
        )

        # Parse IPFS Signal
        ipfs_cid = ipfs_result.get("ipfs_cid")
        ipfs_hash_match = bool(ipfs_result.get("hash_match", False))
        ipfs_retrieval_success = bool(ipfs_result.get("retrieval_success", False))
        ipfs_status = ipfs_result.get("status", "UNVERIFIED")

        ipfs_signal = IPFSSignal(
            cid=ipfs_cid,
            hash_match=ipfs_hash_match,
            retrieval_success=ipfs_retrieval_success,
            status=ipfs_status,
        )

        # Parse Blockchain Signal
        bc_found = bool(blockchain_result.get("blockchain_record_found", False))
        bc_hash_match = bool(blockchain_result.get("hash_match", False))
        bc_tx_id = blockchain_result.get("transaction_id")
        bc_registered_at = blockchain_result.get("registered_at")
        bc_status = blockchain_result.get("integrity_status", "RECORD_NOT_FOUND")

        blockchain_signal = BlockchainSignal(
            record_found=bc_found,
            hash_match=bc_hash_match,
            transaction_id=bc_tx_id,
            registered_at=bc_registered_at,
            status=bc_status,
        )

        # Derive final technical status & explanation
        final_status, explanation = determine_final_status(
            blockchain_found=bc_found,
            blockchain_hash_match=bc_hash_match,
            ipfs_retrieval_success=ipfs_retrieval_success,
            ipfs_hash_match=ipfs_hash_match,
            ml_prediction=ml_pred,
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        # Build details payload for database audit record
        details_json = {
            "ml": ml_result,
            "ipfs": ipfs_result,
            "blockchain": blockchain_result,
            "explanation": explanation,
        }

        # Store in integrity_verifications table
        verification_record = IntegrityVerification(
            document_id=document_id,
            ml_prediction_id=ml_result.get("prediction_id"),
            ipfs_cid=ipfs_cid,
            current_hash=blockchain_result.get("current_hash") or (doc.current_sha256 if doc else None) or (doc.file_hash if doc else None) or "",
            registered_hash=blockchain_result.get("registered_hash"),
            hash_match=bc_hash_match,
            ipfs_match=ipfs_hash_match,
            blockchain_match=bc_found and bc_hash_match,
            final_status=final_status,
            verification_details_json=details_json,
        )
        db.add(verification_record)

        if doc:
            doc.integrity_status = final_status

        db.commit()
        db.refresh(verification_record)

        return IntegratedVerificationResponse(
            document_id=document_id,
            ml=ml_signal,
            ipfs=ipfs_signal,
            blockchain=blockchain_signal,
            integrity=IntegritySignal(status=bc_status),
            final_status=final_status,
            technical_explanation=explanation,
            verification_id=verification_record.id,
            verified_at=now_iso,
        )
