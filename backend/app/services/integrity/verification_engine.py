"""
Unified Verification & Registration Engine (Part D).
Orchestrates the entire multi-stage integrity lifecycle:
Document Upload -> Processing -> Features -> SHA-256 -> IPFS -> Hyperledger Fabric -> Anomaly Detection -> Evidence Verification.
"""
from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_features import DocumentFeatures
from app.models.document_analysis import DocumentAnalysis
from app.services.ipfs.uploader import IPFSUploader
from app.services.ipfs.verifier import IPFSVerifier
from app.services.blockchain.document_registry import DocumentRegistry
from app.services.blockchain.verifier import BlockchainVerifier
from app.services.integrity.evidence_engine import EvidenceEngine
from app.services.integrity.exceptions import IncompleteProcessingError, VerificationProcessingError
from app.services.integrity.schemas import (
    IntegratedRegistrationResponse,
    IntegratedVerificationResponse,
)
from app.ml.advanced.autoencoder.predictor import AutoencoderPredictor
from app.services.feature_engineering.feature_registry import FeatureRegistry

logger = logging.getLogger(__name__)


class VerificationEngine:
    """Coordinates end-to-end registration and technical integrity verification workflows."""

    def __init__(
        self,
        ipfs_uploader: Optional[IPFSUploader] = None,
        ipfs_verifier: Optional[IPFSVerifier] = None,
        blockchain_registry: Optional[DocumentRegistry] = None,
        blockchain_verifier: Optional[BlockchainVerifier] = None,
        evidence_engine: Optional[EvidenceEngine] = None,
        feature_registry: Optional[FeatureRegistry] = None,
    ):
        self.ipfs_uploader = ipfs_uploader or IPFSUploader()
        self.ipfs_verifier = ipfs_verifier or IPFSVerifier()
        self.blockchain_registry = blockchain_registry or DocumentRegistry()
        self.blockchain_verifier = blockchain_verifier or BlockchainVerifier()
        self.evidence_engine = evidence_engine or EvidenceEngine()
        self.feature_registry = feature_registry or FeatureRegistry()

        try:
            self.autoencoder_predictor = AutoencoderPredictor.load()
        except Exception:
            self.autoencoder_predictor = None

    def register_integrity(
        self,
        db: Session,
        document_id: str,
        issuer_reference: str = "Official Government Authority",
        document_version: str = "1.0",
    ) -> IntegratedRegistrationResponse:
        """
        Executes end-to-end registration:
        Preprocessing check -> Feature check -> IPFS upload -> Hyperledger registration.
        """
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise IncompleteProcessingError(f"Document {document_id} not found in database.")

        # 1. Require Phase 2 preprocessing completion
        if doc.processing_status != "completed" or not doc.analysis:
            raise IncompleteProcessingError(
                f"Document {document_id} preprocessing must be completed before blockchain registration. Current status: {doc.processing_status}"
            )

        # 2. Check Phase 3 feature engineering
        feat = db.query(DocumentFeatures).filter(DocumentFeatures.document_id == document_id).first()
        features_generated = feat is not None

        # 3. Read file and compute SHA-256
        file_path = Path(doc.file_path)
        if not file_path.exists():
            raise IncompleteProcessingError(f"Document file missing from disk at {file_path}")

        with open(file_path, "rb") as f:
            content_bytes = f.read()
        sha256_hash = hashlib.sha256(content_bytes).hexdigest()

        # 4. Upload to IPFS
        ipfs_res = self.ipfs_uploader.upload_document(db, document_id)
        cid = ipfs_res.ipfs_cid

        # 5. Register on Hyperledger Fabric
        bc_res = self.blockchain_registry.register_document(
            db=db,
            document_id=document_id,
            issuer_reference=issuer_reference,
            document_version=document_version,
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        return IntegratedRegistrationResponse(
            success=True,
            document_id=document_id,
            preprocessing_status="completed",
            features_generated=features_generated,
            ipfs_cid=cid,
            document_hash=sha256_hash,
            blockchain_tx_id=bc_res.transaction_id,
            final_status="REGISTERED",
            registered_at=now_iso,
        )

    def verify_integrity(
        self,
        db: Session,
        document_id: str,
    ) -> IntegratedVerificationResponse:
        """
        Executes complete multi-signal technical verification:
        1. PyTorch Autoencoder Anomaly Scoring
        2. IPFS CID & Content Hash Check
        3. Hyperledger Fabric Blockchain Hash Verification
        4. Evidence Consolidation and Audit Trail Creation
        """
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise VerificationProcessingError(f"Document {document_id} not found.")

        # 1. Run ML Anomaly Detection
        ml_result: Dict[str, Any] = {
            "model": "Autoencoder",
            "model_version": "1.0.0",
            "reconstruction_error": 0.0,
            "anomaly_score": 0.0,
            "prediction": 0,
        }

        feat_record = (
            db.query(DocumentFeatures).filter(DocumentFeatures.document_id == document_id).first()
        )
        if feat_record and feat_record.feature_vector and self.autoencoder_predictor is not None:
            try:
                raw_vec = feat_record.feature_vector
                vector = np.array(raw_vec, dtype=np.float32)
                expected_dim = self.autoencoder_predictor.expected_dimension

                # Pad or slice to match expected feature dimension if necessary
                if len(vector) < expected_dim:
                    padded = np.zeros(expected_dim, dtype=np.float32)
                    padded[: len(vector)] = vector
                    vector = padded
                elif len(vector) > expected_dim:
                    vector = vector[:expected_dim]

                ml_result = self.autoencoder_predictor.predict(
                    vector, document_id=document_id, db=db
                )
            except Exception as e:
                logger.warning(f"Autoencoder prediction error for {document_id}: {e}")

        # 2. Run IPFS Verification
        ipfs_verify_res = self.ipfs_verifier.verify_document_ipfs(db, document_id)
        ipfs_result = ipfs_verify_res.dict()

        # 3. Run Blockchain Verification
        bc_verify_res = self.blockchain_verifier.verify_document(db, document_id)
        blockchain_result = bc_verify_res.dict()

        # 4. Compile Ev
        return self.evidence_engine.compile_evidence(
            db=db,
            document_id=document_id,
            ml_result=ml_result,
            ipfs_result=ipfs_result,
            blockchain_result=blockchain_result,
        )
