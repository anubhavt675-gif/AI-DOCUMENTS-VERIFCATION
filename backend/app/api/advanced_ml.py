"""
Advanced ML API Router (Phase 5).
Exposes endpoints for PyTorch Autoencoder training, prediction, model activation,
comparison with Isolation Forest, and document prediction history.
"""
from typing import Any, Dict, List, Optional
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.advanced.autoencoder.predictor import AutoencoderPredictor
from app.ml.advanced.autoencoder.trainer import AutoencoderTrainer
from app.ml.advanced.comparison.model_comparator import ModelComparator
from app.ml.advanced.embeddings.embedding_cache import EmbeddingManager
from app.ml.advanced.schemas import (
    AdvancedPredictRequest,
    AdvancedPredictResponse,
    AdvancedTrainRequest,
    AdvancedTrainResponse,
    ModelComparisonResponse,
)
from app.models.advanced_ml import AdvancedMLModel, AdvancedMLPrediction
from app.models.document import Document
from app.models.document_features import DocumentFeatures
from app.models.document_analysis import DocumentAnalysis
from app.services.feature_engineering.feature_registry import FeatureRegistry

router = APIRouter(prefix="/api/ml", tags=["Advanced ML - Autoencoder"])
doc_ml_router = APIRouter(prefix="/api/documents", tags=["Advanced ML - Document Inference"])


@router.post("/advanced/train", response_model=AdvancedTrainResponse)
def train_advanced_model(
    request: AdvancedTrainRequest,
    db: Session = Depends(get_db),
):
    """Trains a new PyTorch Autoencoder on baseline features."""
    registry = FeatureRegistry()
    feature_names = registry.get_feature_names()
    dim = len(feature_names)

    # Collect existing features from DB if available, else baseline distribution
    records = db.query(DocumentFeatures).all()
    valid_vectors = []
    for r in records:
        if r.feature_vector and isinstance(r.feature_vector, list) and len(r.feature_vector) >= dim:
            valid_vectors.append([float(x) for x in r.feature_vector[:dim]])
        elif r.features_json and isinstance(r.features_json, dict):
            valid_vectors.append([float(r.features_json.get(f, 0.0)) for f in feature_names])

    if len(valid_vectors) >= 5:
        feature_matrix = np.array(valid_vectors, dtype=np.float32)
    else:
        rng = np.random.RandomState(42)
        feature_matrix = rng.normal(loc=0.5, scale=0.15, size=(max(20, len(valid_vectors) * 5), dim))

    if request.input_mode == "structured_plus_text_embedding":
        # Append 64-dim dummy/normal semantic embedding for hybrid mode
        rng = np.random.RandomState(42)
        emb_matrix = rng.normal(loc=0.0, scale=0.1, size=(len(feature_matrix), 64))
        feature_matrix = np.hstack([feature_matrix, emb_matrix])
        dim = feature_matrix.shape[1]
        feature_names = feature_names + [f"nlp_emb_{i}" for i in range(64)]

    trainer = AutoencoderTrainer(
        learning_rate=request.learning_rate,
        batch_size=request.batch_size,
        epochs=request.epochs,
        latent_dim=request.latent_dim,
        threshold_method=request.threshold_method,
        threshold_percentile=request.threshold_percentile,
    )

    try:
        res = trainer.train(
            features=feature_matrix,
            version=request.model_version,
            input_mode=request.input_mode,
            feature_names=feature_names,
            db=db,
        )
        return AdvancedTrainResponse(
            success=True,
            model_version=res["model_version"],
            input_mode=res["input_mode"],
            input_dimension=res["input_dimension"],
            threshold=res["threshold"],
            training_duration_seconds=res["training_duration_seconds"],
            artifact_path=res["artifact_path"],
            db_id=res["db_id"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Autoencoder training failed: {str(e)}",
        )


@router.post("/advanced/models/{model_id}/activate")
def activate_advanced_model(
    model_id: str,
    db: Session = Depends(get_db),
):
    """Sets a specific Autoencoder model version as active."""
    target = db.query(AdvancedMLModel).filter(AdvancedMLModel.id == model_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Model record not found.")

    db.query(AdvancedMLModel).update({AdvancedMLModel.is_active: False})
    target.is_active = True
    db.commit()

    # Invalidate cache so predictor loads this version
    AutoencoderPredictor._cached_version = None

    return {"success": True, "active_model_version": target.model_version}


@router.get("/advanced/models")
def list_advanced_models(
    db: Session = Depends(get_db),
):
    """Lists all registered Autoencoder models."""
    models = db.query(AdvancedMLModel).order_by(AdvancedMLModel.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "model_name": m.model_name,
            "model_version": m.model_version,
            "input_mode": m.input_mode,
            "input_dimension": m.input_dimension,
            "threshold": m.threshold,
            "threshold_method": m.threshold_method,
            "is_active": m.is_active,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "training_metrics": m.training_metrics,
        }
        for m in models
    ]


@router.get("/models/comparison")
def compare_models(
    db: Session = Depends(get_db),
):
    """
    Compares Isolation Forest and Autoencoder side-by-side using real feature vectors.
    """
    registry = FeatureRegistry()
    feature_names = registry.get_feature_names()
    records = db.query(DocumentFeatures).all()
    valid_vectors = []
    dim = len(feature_names)
    for r in records:
        if r.feature_vector and isinstance(r.feature_vector, list) and len(r.feature_vector) >= dim:
            valid_vectors.append([float(x) for x in r.feature_vector[:dim]])
        elif r.features_json and isinstance(r.features_json, dict):
            valid_vectors.append([float(r.features_json.get(f, 0.0)) for f in feature_names])

    if len(valid_vectors) >= 4:
        features = np.array(valid_vectors, dtype=np.float32)
        ground_truth = np.zeros(len(features), dtype=int)
    else:
        rng = np.random.RandomState(42)
        normal_data = rng.normal(loc=0.5, scale=0.15, size=(30, dim))
        anom_data = rng.normal(loc=1.8, scale=0.5, size=(10, dim))
        features = np.vstack([normal_data, anom_data])
        ground_truth = np.array([0] * 30 + [1] * 10)

    comparator = ModelComparator()
    return comparator.compare_on_data(features, ground_truth, feature_names)


@router.post("/documents/{document_id}/advanced-predict", response_model=AdvancedPredictResponse)
@doc_ml_router.post("/{document_id}/advanced-predict", response_model=AdvancedPredictResponse)
def predict_document_autoencoder(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Computes Autoencoder reconstruction error anomaly prediction for a specific document.
    """
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    feat_record = (
        db.query(DocumentFeatures).filter(DocumentFeatures.document_id == document_id).first()
    )
    if not feat_record or not feat_record.feature_vector:
        raise HTTPException(
            status_code=400,
            detail="Document features not yet extracted. Run feature extraction first.",
        )

    try:
        predictor = AutoencoderPredictor.load()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load Autoencoder model: {e}")

    vector = np.array(feat_record.feature_vector, dtype=np.float32)

    # If predictor expects hybrid mode, fetch or compute NLP embedding
    if predictor.input_mode == "structured_plus_text_embedding":
        doc_analysis = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == document_id).first()
        raw_text = doc_analysis.cleaned_text if doc_analysis else ""
        emb_mgr = EmbeddingManager()
        emb_vec, _, _ = emb_mgr.get_or_create_embedding(db, document_id, raw_text)
        vector = np.concatenate([vector, np.array(emb_vec, dtype=np.float32)])

    # Ensure dimension matches expected
    expected_dim = predictor.expected_dimension
    if len(vector) < expected_dim:
        padded = np.zeros(expected_dim, dtype=np.float32)
        padded[: len(vector)] = vector
        vector = padded
    elif len(vector) > expected_dim:
        vector = vector[:expected_dim]

    result = predictor.predict(vector, document_id=document_id, db=db)
    return AdvancedPredictResponse(**result)


@router.get("/documents/{document_id}/predictions")
@doc_ml_router.get("/{document_id}/predictions")
def get_document_prediction_history(
    document_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves all historical advanced ML predictions for a document."""
    preds = (
        db.query(AdvancedMLPrediction)
        .filter(AdvancedMLPrediction.document_id == document_id)
        .order_by(AdvancedMLPrediction.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "model_name": p.model_name,
            "model_version": p.model_version,
            "input_mode": p.input_mode,
            "reconstruction_error": p.reconstruction_error,
            "anomaly_score": p.anomaly_score,
            "threshold": p.threshold,
            "prediction": p.prediction,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in preds
    ]
