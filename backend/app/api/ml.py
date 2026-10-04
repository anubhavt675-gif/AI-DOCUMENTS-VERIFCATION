"""
Machine Learning API Endpoints (Phase 4).
Covers training, model registry management, batch predictions, and monitoring stats.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.ml.config import LEGAL_FORENSIC_DISCLAIMER
from app.ml.inference.predictor import AnomalyPredictor
from app.ml.model_registry.registry import ModelRegistryService
from app.ml.schemas import (
    BatchPredictRequest,
    BatchPredictResponse,
    MLModelResponse,
    MLMonitoringStatsResponse,
    TrainModelRequest,
)
from app.ml.training.trainer import ModelTrainer
from app.models.ml_model import MLModel
from app.models.ml_prediction import MLPrediction

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])

# Singleton services
_trainer = ModelTrainer()
_registry_service = ModelRegistryService()
_predictor = AnomalyPredictor(registry_service=_registry_service)


@router.post("/train", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def train_model(
    request: TrainModelRequest = TrainModelRequest(),
    db: Session = Depends(get_db),
):
    """
    Train an Isolation Forest anomaly detection model using existing Phase 3 feature vectors.
    Saves model artifacts, fits scaler on training split strictly, computes baseline statistics,
    and registers the model in the model registry.
    """
    try:
        result = _trainer.train(db, request)
        # Clear cached model so new active model loads
        _registry_service.clear_cache()
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {str(e)}",
        )


@router.get("/models", response_model=List[MLModelResponse])
def list_models(db: Session = Depends(get_db)):
    """List all registered ML models with their configurations, versions, and metrics."""
    models = _registry_service.list_models(db)
    return [
        MLModelResponse(
            id=m.id,
            model_name=m.model_name,
            model_version=m.model_version,
            feature_version=m.feature_version,
            model_type=m.model_type,
            is_active=m.is_active,
            training_sample_count=m.training_sample_count,
            configuration=m.configuration_json or {},
            metrics=m.metrics_json,
            feature_names=m.feature_names_json or [],
            description=m.description,
            created_at=m.created_at,
        )
        for m in models
    ]


@router.get("/models/active", response_model=Optional[MLModelResponse])
def get_active_model(
    model_name: str = Query(default="IsolationForest"),
    db: Session = Depends(get_db),
):
    """Fetch the currently active model record for production inference."""
    m = _registry_service.get_active_model(db, model_name=model_name)
    if not m:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active model found for '{model_name}'. Train a model first via POST /api/ml/train.",
        )
    return MLModelResponse(
        id=m.id,
        model_name=m.model_name,
        model_version=m.model_version,
        feature_version=m.feature_version,
        model_type=m.model_type,
        is_active=m.is_active,
        training_sample_count=m.training_sample_count,
        configuration=m.configuration_json or {},
        metrics=m.metrics_json,
        feature_names=m.feature_names_json or [],
        description=m.description,
        created_at=m.created_at,
    )


@router.post("/models/{model_id}/activate", response_model=MLModelResponse)
def activate_model(model_id: str, db: Session = Depends(get_db)):
    """Activate a specific model version for production inference."""
    try:
        m = _registry_service.activate_model(model_id, db)
        _registry_service.clear_cache()
        return MLModelResponse(
            id=m.id,
            model_name=m.model_name,
            model_version=m.model_version,
            feature_version=m.feature_version,
            model_type=m.model_type,
            is_active=m.is_active,
            training_sample_count=m.training_sample_count,
            configuration=m.configuration_json or {},
            metrics=m.metrics_json,
            feature_names=m.feature_names_json or [],
            description=m.description,
            created_at=m.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate model: {str(e)}",
        )


@router.post("/predict-batch", response_model=BatchPredictResponse)
def predict_batch(
    request: BatchPredictRequest,
    custom_threshold: Optional[float] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Run anomaly detection on a batch of document IDs.
    Returns successful predictions and specific error messages for failed documents.
    """
    try:
        return _predictor.predict_batch(
            document_ids=request.document_ids,
            db=db,
            custom_threshold=custom_threshold,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}",
        )


@router.get("/monitoring", response_model=MLMonitoringStatsResponse)
def get_monitoring_stats(db: Session = Depends(get_db)):
    """
    Retrieve real monitoring statistics calculated from actual prediction records.
    No mock data.
    """
    total = db.query(MLPrediction).count()
    normal = db.query(MLPrediction).filter(MLPrediction.prediction == 0).count()
    anomalous = db.query(MLPrediction).filter(MLPrediction.prediction == 1).count()
    
    avg_score_res = db.query(func.avg(MLPrediction.anomaly_score)).scalar()
    avg_score = float(avg_score_res) if avg_score_res is not None else 0.0

    # Model breakdown
    breakdown_rows = (
        db.query(MLPrediction.model_version, func.count(MLPrediction.id))
        .group_by(MLPrediction.model_version)
        .all()
    )
    breakdown = {str(version): int(cnt) for version, cnt in breakdown_rows}

    # Active model info
    active_m = _registry_service.get_active_model(db)
    active_dict = None
    if active_m:
        active_dict = {
            "id": active_m.id,
            "model_name": active_m.model_name,
            "model_version": active_m.model_version,
            "feature_version": active_m.feature_version,
            "training_samples": active_m.training_sample_count,
            "created_at": active_m.created_at.isoformat(),
        }

    return MLMonitoringStatsResponse(
        total_predictions=total,
        normal_count=normal,
        anomalous_count=anomalous,
        anomaly_ratio=round(anomalous / total, 4) if total > 0 else 0.0,
        average_anomaly_score=round(avg_score, 4),
        model_breakdown=breakdown,
        active_model=active_dict,
    )
