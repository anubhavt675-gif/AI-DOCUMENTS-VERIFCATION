"""
Tampering Simulation & Synthetic Dataset API (Prototype Demo).
Provides:
  1. POST /api/demo/tamper/{document_id}    — Simulate document tampering
  2. GET  /api/demo/synthetic-dataset       — Generate labeled synthetic training data
  3. POST /api/demo/seed-training-data      — Inject synthetic data into DB for model training

All synthetic data is clearly labeled as prototype/demo data.
"""
import hashlib
import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.models.document_features import DocumentFeatures
from app.services.document_service import get_document_by_document_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["Prototype Demo"])

SYNTHETIC_LABEL = "⚠️ PROTOTYPE / SYNTHETIC DATASET — Not real government documents"


# ── Synthetic Feature Generator ─────────────────────────────────────────────

def _make_normal_features(seed: int = 0) -> Dict[str, float]:
    """Generate a feature vector typical of a NORMAL (authentic) document."""
    rng = random.Random(seed)
    return {
        # File metrics
        "file_size_bytes": rng.uniform(50_000, 2_000_000),
        "file_size_log": rng.uniform(10.8, 14.5),
        # Text
        "word_count": rng.uniform(300, 5000),
        "character_count": rng.uniform(1500, 30_000),
        "paragraph_count": rng.uniform(10, 80),
        "avg_word_length": rng.uniform(4.5, 6.5),
        "type_token_ratio": rng.uniform(0.55, 0.80),
        "stopword_ratio": rng.uniform(0.30, 0.50),
        "digit_ratio": rng.uniform(0.02, 0.10),
        "uppercase_ratio": rng.uniform(0.05, 0.15),
        "punctuation_ratio": rng.uniform(0.02, 0.07),
        "sentence_count": rng.uniform(20, 300),
        "avg_sentence_length": rng.uniform(12, 25),
        # Structure
        "page_count": rng.uniform(1, 20),
        "total_text_blocks": rng.uniform(5, 100),
        "total_images": rng.uniform(0, 5),
        "total_links": rng.uniform(0, 10),
        "font_count": rng.uniform(1, 5),
        "heading_count": rng.uniform(2, 20),
        "table_count": rng.uniform(0, 5),
        # Metadata
        "metadata_completeness": rng.uniform(0.60, 1.0),
        "has_title": rng.choice([0.0, 1.0]),
        "has_author": 1.0,
        "has_creation_date": 1.0,
        "has_modification_date": 1.0,
        "metadata_field_count": rng.uniform(5, 9),
        # Timestamps
        "days_since_creation": rng.uniform(1, 3650),
        "days_since_modification": rng.uniform(0, 30),
        "modification_count": rng.uniform(1, 5),
        "timestamp_suspicious": 0.0,
        "creation_before_modification": 1.0,
        # Integrity
        "hash_present": 1.0,
        "extension_mime_consistent": 1.0,
        "structural_consistency": rng.uniform(0.85, 1.0),
        # Padding to 85 features
        **{f"feat_{i:02d}": rng.gauss(0, 1) for i in range(50)},
    }


def _make_anomalous_features(seed: int = 0, anomaly_type: str = "tampered") -> Dict[str, float]:
    """Generate a feature vector typical of an ANOMALOUS (suspicious) document."""
    rng = random.Random(seed + 10000)
    base = _make_normal_features(seed)

    if anomaly_type == "tampered":
        # Hash mismatch + timestamp inconsistency
        base["hash_present"] = 0.0
        base["timestamp_suspicious"] = 1.0
        base["days_since_modification"] = rng.uniform(0, 0.1)  # Modified very recently
        base["modification_count"] = rng.uniform(10, 50)  # Too many edits
        base["structural_consistency"] = rng.uniform(0.0, 0.3)
        base["extension_mime_consistent"] = 0.0
    elif anomaly_type == "metadata_stripped":
        base["metadata_completeness"] = rng.uniform(0.0, 0.2)
        base["has_author"] = 0.0
        base["has_creation_date"] = 0.0
        base["metadata_field_count"] = rng.uniform(0, 2)
    elif anomaly_type == "format_anomaly":
        base["page_count"] = 0.0
        base["total_text_blocks"] = 0.0
        base["word_count"] = rng.uniform(0, 5)
        base["structural_consistency"] = rng.uniform(0.0, 0.2)
    elif anomaly_type == "suspicious_content":
        base["digit_ratio"] = rng.uniform(0.4, 0.8)  # Abnormally high digit ratio
        base["uppercase_ratio"] = rng.uniform(0.5, 0.9)
        base["type_token_ratio"] = rng.uniform(0.05, 0.2)  # Very low vocabulary variety

    return base


# ── API Endpoints ────────────────────────────────────────────────────────────

@router.post("/tamper/{document_id}")
def simulate_tampering(
    document_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Simulate document tampering for prototype demonstration.

    Workflow:
    1. Retrieve the document's original registered hash
    2. Generate a 'tampered' hash by modifying content
    3. Return comparison showing HASH MISMATCH
    4. Recalculate anomaly score based on tampering signals

    NOTE: This does NOT modify the actual file on disk.
    It demonstrates what WOULD happen if someone tampered with the document.
    """
    doc = get_document_by_document_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    original_hash = doc.current_sha256 or doc.file_hash or "N/A"

    # Simulate a tampered version hash (as if someone modified the file content)
    # We demonstrate this by computing hash of slightly-altered content
    tampered_seed = f"{document_id}-tampered-{datetime.now(timezone.utc).isoformat()}"
    tampered_hash = hashlib.sha256(tampered_seed.encode()).hexdigest()

    # Check if document is registered on blockchain
    from app.services.blockchain.fabric_client import FabricClient
    fabric = FabricClient()
    blockchain_registered = False
    registered_hash = None

    try:
        record = fabric.get_document(document_id)
        registered_hash = record.get("document_hash")
        blockchain_registered = True
    except Exception:
        pass

    hash_match = bool(registered_hash and original_hash == registered_hash)

    # Anomaly signals for tampering demonstration
    anomaly_indicators = [
        "Metadata modification timestamp inconsistency detected",
        "Document structural hash deviated from registered baseline",
        "Modification frequency exceeds normal government document patterns",
        "Author metadata field altered after initial registration",
    ]

    # Compute a simulated anomaly score for demonstration
    anomaly_score = 0.82  # High score = tampered document

    return {
        "document_id": document_id,
        "prototype_note": SYNTHETIC_LABEL,
        "tampering_simulation": {
            "original_filename": doc.original_filename,
            "original_hash": original_hash,
            "simulated_tampered_hash": tampered_hash,
            "hash_mismatch": True,
            "mismatch_type": "CONTENT_MODIFICATION_SIMULATED",
        },
        "blockchain_check": {
            "registered": blockchain_registered,
            "registered_hash": registered_hash,
            "current_hash": original_hash,
            "hash_match": hash_match,
            "status": "MATCH" if hash_match else ("HASH_MISMATCH" if registered_hash else "NOT_REGISTERED"),
        },
        "anomaly_analysis": {
            "anomaly_score": anomaly_score,
            "risk_level": "CRITICAL",
            "anomaly_score_0_to_100": int(anomaly_score * 100),
            "detected_issues": anomaly_indicators,
            "final_verdict": "⚠️ POSSIBLE DOCUMENT TAMPERING DETECTED",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/synthetic-dataset")
def get_synthetic_dataset(
    n_normal: int = 80,
    n_anomalous: int = 20,
) -> Dict[str, Any]:
    """
    Generate a clearly labeled synthetic dataset for model training demonstration.

    Returns a balanced dataset with feature vectors for:
    - Normal (authentic) government documents
    - Anomalous (tampered/suspicious) documents

    IMPORTANT: This is PROTOTYPE/SYNTHETIC data, NOT real government documents.
    """
    n_normal = min(n_normal, 200)
    n_anomalous = min(n_anomalous, 100)

    records = []
    anomaly_types = ["tampered", "metadata_stripped", "format_anomaly", "suspicious_content"]

    for i in range(n_normal):
        features = _make_normal_features(seed=i)
        records.append({
            "document_id": f"synth_normal_{i:04d}",
            "label": 0,
            "label_name": "NORMAL",
            "features": features,
            "synthetic": True,
        })

    for i in range(n_anomalous):
        atype = anomaly_types[i % len(anomaly_types)]
        features = _make_anomalous_features(seed=i, anomaly_type=atype)
        records.append({
            "document_id": f"synth_anomalous_{i:04d}",
            "label": 1,
            "label_name": "ANOMALOUS",
            "anomaly_type": atype,
            "features": features,
            "synthetic": True,
        })

    return {
        "prototype_note": SYNTHETIC_LABEL,
        "total_records": len(records),
        "normal_count": n_normal,
        "anomalous_count": n_anomalous,
        "contamination_rate": round(n_anomalous / (n_normal + n_anomalous), 3),
        "feature_count": len(records[0]["features"]) if records else 0,
        "records": records,
    }


@router.post("/seed-training-data")
def seed_synthetic_training_data(
    n_normal: int = 60,
    n_anomalous: int = 15,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Inject synthetic document feature records into the database so the
    ML model can be trained even with no real uploaded documents.

    Clearly marks all records as synthetic/prototype data.
    IMPORTANT: Use only for prototype/demo purposes.
    """
    from app.services.feature_engineering import FEATURE_VERSION
    from app.models.document import Document as DocModel
    from app.models.document_features import DocumentFeatures

    n_normal = min(n_normal, 150)
    n_anomalous = min(n_anomalous, 75)
    anomaly_types = ["tampered", "metadata_stripped", "format_anomaly", "suspicious_content"]

    created_docs = 0
    created_features = 0

    all_records = []

    for i in range(n_normal):
        all_records.append((f"synth_normal_{i:04d}", 0, "NORMAL", _make_normal_features(seed=i + 1000)))
    for i in range(n_anomalous):
        atype = anomaly_types[i % len(anomaly_types)]
        all_records.append((f"synth_anom_{i:04d}", 1, "ANOMALOUS", _make_anomalous_features(seed=i + 2000, anomaly_type=atype)))

    now = datetime.now(timezone.utc)
    feature_names = sorted(list(all_records[0][3].keys())) if all_records else []

    for doc_id, label, label_name, features_dict in all_records:
        # Create synthetic document record if not exists
        existing = db.query(DocModel).filter(DocModel.document_id == doc_id).first()
        if not existing:
            synth_doc = DocModel(
                document_id=doc_id,
                original_filename=f"synthetic_{doc_id}.txt",
                stored_filename=f"synthetic_{doc_id}.txt",
                file_type="text/plain",
                file_size=random.randint(5000, 500_000),
                status="verified" if label == 0 else "suspicious",
                processing_status="completed",
                file_hash=hashlib.sha256(doc_id.encode()).hexdigest(),
                hash_algorithm="SHA-256",
                current_sha256=hashlib.sha256(doc_id.encode()).hexdigest(),
                integrity_status="SYNTHETIC",
                created_at=now,
            )
            db.add(synth_doc)
            created_docs += 1

        # Create feature record if not exists
        existing_feat = db.query(DocumentFeatures).filter(DocumentFeatures.document_id == doc_id).first()
        if not existing_feat:
            feat_record = DocumentFeatures(
                document_id=doc_id,
                feature_version=FEATURE_VERSION,
                features_json=features_dict,
                feature_names_json=feature_names,
                feature_dimension=len(feature_names),
                extraction_timestamp=now,
                created_at=now,
            )
            db.add(feat_record)
            created_features += 1

    db.commit()



    return {
        "prototype_note": SYNTHETIC_LABEL,
        "status": "completed",
        "documents_created": created_docs,
        "feature_records_created": created_features,
        "total_normal": n_normal,
        "total_anomalous": n_anomalous,
        "feature_version": FEATURE_VERSION,
        "message": f"Injected {created_features} synthetic feature records. You can now train the ML model.",
    }


@router.get("/system-status")
def get_system_status() -> Dict[str, Any]:
    """
    Returns overall prototype system status for the dashboard.
    Shows which components are available vs simulated.
    """
    from app.services.blockchain.fabric_client import FabricClient
    from app.services.ipfs.client import IPFSClient

    fabric = FabricClient()
    ipfs = IPFSClient()

    return {
        "prototype_note": SYNTHETIC_LABEL,
        "components": {
            "document_upload": {"status": "OPERATIONAL", "mode": "real"},
            "document_preprocessing": {"status": "OPERATIONAL", "mode": "real"},
            "metadata_extraction": {"status": "OPERATIONAL", "mode": "real"},
            "feature_engineering": {"status": "OPERATIONAL", "mode": "real"},
            "isolation_forest_ml": {"status": "OPERATIONAL", "mode": "real"},
            "hash_generation": {"status": "OPERATIONAL", "mode": "real"},
            "blockchain_ledger": {
                "status": "SIMULATED",
                "mode": "local_json_ledger",
                "note": "Hyperledger Fabric peer not deployed — using cryptographic JSON simulation",
                "peer_reachable": fabric.is_peer_reachable(),
            },
            "ipfs_storage": {
                "status": "SIMULATED" if not ipfs.check_daemon_status() else "OPERATIONAL",
                "mode": "local_content_store" if not ipfs.check_daemon_status() else "kubo_daemon",
                "note": "Using local CIDv0-addressed blockstore" if not ipfs.check_daemon_status() else "Connected to Kubo IPFS daemon",
                "daemon_active": ipfs.check_daemon_status(),
            },
            "hyperledger_fabric_network": {
                "status": "NOT_DEPLOYED",
                "note": "Full Hyperledger Fabric network requires peer/orderer deployment",
            },
        },
        "overall_prototype_readiness": "DEMO_READY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
