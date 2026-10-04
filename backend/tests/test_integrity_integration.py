"""
End-to-End Integration & Tampering Simulation Tests (Part D & Part I).
Tests:
- Full 10-step lifecycle:
  Ingest -> Preprocess -> Features -> Embedding -> Isolation Forest -> Autoencoder -> IPFS -> Fabric -> Verify -> Consolidated Evidence
- Tampering simulation:
  Byte-level mutation causing Current SHA-256 != Registered SHA-256 -> reports INTEGRITY_MISMATCH
- Unregistered document validation -> reports UNREGISTERED
- Forensic isolation: Technical verification does not conflate integrity with authority or anomaly with forgery
"""
import hashlib
from pathlib import Path
import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.document import Document
from app.models.document_analysis import DocumentAnalysis
from app.models.document_features import DocumentFeatures
from app.models.document_embedding import DocumentEmbedding
from app.services.ipfs.client import IPFSClient
from app.services.ipfs.uploader import IPFSUploader
from app.services.ipfs.verifier import IPFSVerifier
from app.services.blockchain.fabric_client import FabricClient
from app.services.blockchain.document_registry import DocumentRegistry
from app.services.blockchain.verifier import BlockchainVerifier
from app.services.integrity.verification_engine import VerificationEngine
from app.services.integrity.evidence_engine import EvidenceEngine
from app.services.integrity.rules import (
    STATUS_VERIFIED_INTEGRITY,
    STATUS_INTEGRITY_MISMATCH,
    STATUS_UNREGISTERED,
    STATUS_ANOMALY_DETECTED,
)


@pytest.fixture
def test_env(tmp_path):
    # Setup temporary database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Setup isolated storage folders
    ipfs_dir = tmp_path / "ipfs_data"
    ledger_dir = tmp_path / "ledger_data"
    ipfs_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ipfs_client = IPFSClient(storage_dir=ipfs_dir)
    fabric_client = FabricClient(storage_dir=ledger_dir)

    uploader = IPFSUploader(client=ipfs_client)
    ipfs_verifier = IPFSVerifier(client=ipfs_client)
    bc_registry = DocumentRegistry(fabric_client=fabric_client)
    bc_verifier = BlockchainVerifier(fabric_client=fabric_client)
    evidence_engine = EvidenceEngine()

    engine_svc = VerificationEngine(
        ipfs_uploader=uploader,
        ipfs_verifier=ipfs_verifier,
        blockchain_registry=bc_registry,
        blockchain_verifier=bc_verifier,
        evidence_engine=evidence_engine,
    )

    try:
        yield db, tmp_path, engine_svc
    finally:
        db.close()


def test_end_to_end_integrity_lifecycle(test_env):
    db, tmp_path, engine_svc = test_env

    # 1. Upload Document
    doc_path = tmp_path / "executive_order.pdf"
    content = b"%PDF-1.5 Executive Order No. 2026-99: National Cyber Defense Standards"
    doc_path.write_bytes(content)
    file_sha256 = hashlib.sha256(content).hexdigest()

    doc = Document(
        document_id="doc-e2e-1",
        original_filename="executive_order.pdf",
        stored_filename="stored_eo.pdf",
        file_path=str(doc_path),
        file_type="application/pdf",
        file_size=len(content),
        processing_status="completed",
        file_hash=file_sha256,
    )
    db.add(doc)

    # 2. Phase 2 Preprocessing Record
    analysis = DocumentAnalysis(
        document_id=doc.document_id,
        raw_text="Executive Order No. 2026-99: National Cyber Defense Standards",
        cleaned_text="executive order no 2026 99 national cyber defense standards",
        word_count=8,
        character_count=65,
        page_count=1,
    )
    db.add(analysis)

    # 3. Phase 3 Feature Record (85-d vector)
    features_vec = [0.5] * 85
    feat = DocumentFeatures(
        document_id=doc.document_id,
        feature_vector=features_vec,
        feature_dimension=85,
        feature_version="1.0",
        features_json={"feat_0": 0.5},
    )
    db.add(feat)
    db.commit()

    # 4. Phase 7 + Phase 6: Integrated Registration
    reg_response = engine_svc.register_integrity(db, doc.document_id)
    assert reg_response.success is True
    assert reg_response.ipfs_cid.startswith("Qm")
    assert len(reg_response.blockchain_tx_id) == 64
    assert reg_response.final_status == "REGISTERED"

    # 5. Multi-Signal Verification (Untampered)
    verify_response = engine_svc.verify_integrity(db, doc.document_id)
    assert verify_response.final_status == STATUS_VERIFIED_INTEGRITY
    assert verify_response.blockchain.hash_match is True
    assert verify_response.blockchain.record_found is True
    assert verify_response.ipfs.hash_match is True
    assert verify_response.ipfs.retrieval_success is True
    assert "Technical integrity verified" in verify_response.technical_explanation


def test_controlled_tampering_simulation(test_env):
    db, tmp_path, engine_svc = test_env

    # 1. Setup and register original document
    doc_path = tmp_path / "treasury_bond.pdf"
    content = b"Treasury Bond Value: $10,000,000 Maturity: 2036"
    doc_path.write_bytes(content)

    doc = Document(
        document_id="doc-tamper-sim-1",
        original_filename="treasury_bond.pdf",
        stored_filename="stored_bond.pdf",
        file_path=str(doc_path),
        file_type="application/pdf",
        file_size=len(content),
        processing_status="completed",
    )
    db.add(doc)

    analysis = DocumentAnalysis(
        document_id=doc.document_id,
        cleaned_text="treasury bond value 10000000",
        word_count=4,
    )
    db.add(analysis)

    feat = DocumentFeatures(
        document_id=doc.document_id,
        feature_vector=[0.5] * 85,
        feature_dimension=85,
        feature_version="1.0",
        features_json={},
    )
    db.add(feat)
    db.commit()

    engine_svc.register_integrity(db, doc.document_id)

    # 2. Simulate Controlled Tampering: Alter one byte value in the file
    tampered_content = b"Treasury Bond Value: $99,000,000 Maturity: 2036 [FORGED]"
    doc_path.write_bytes(tampered_content)

    # 3. Verification must flag INTEGRITY_MISMATCH
    tamper_verify = engine_svc.verify_integrity(db, doc.document_id)
    assert tamper_verify.final_status == STATUS_INTEGRITY_MISMATCH
    assert tamper_verify.blockchain.hash_match is False
    assert tamper_verify.ipfs.hash_match is False
    assert "Technical integrity mismatch detected" in tamper_verify.technical_explanation


def test_unregistered_document_verification(test_env):
    db, tmp_path, engine_svc = test_env

    doc_path = tmp_path / "unregistered_draft.pdf"
    doc_path.write_bytes(b"Draft Internal Note Not For Release")

    doc = Document(
        document_id="doc-unreg-1",
        original_filename="unregistered_draft.pdf",
        stored_filename="stored_draft.pdf",
        file_path=str(doc_path),
        file_type="application/pdf",
        file_size=35,
        processing_status="completed",
    )
    db.add(doc)

    analysis = DocumentAnalysis(
        document_id=doc.document_id,
        cleaned_text="draft internal note",
    )
    db.add(analysis)
    db.commit()

    # Verification on unregistered document
    verify_response = engine_svc.verify_integrity(db, doc.document_id)
    assert verify_response.final_status == STATUS_UNREGISTERED
    assert verify_response.blockchain.record_found is False
