"""
Inference engine for PyTorch Autoencoder (Phase 5).
Computes exact reconstruction error, normalizes anomaly score, and returns technical prediction:
0 = NORMAL
1 = ANOMALOUS
"""
import logging
from typing import Any, Dict, List, Optional
import numpy as np
import torch
from sqlalchemy.orm import Session

from app.ml.advanced.autoencoder.model import DocumentAutoencoder
from app.ml.advanced.autoencoder.scoring import compute_reconstruction_errors, score_anomaly
from app.ml.advanced.utils.checkpoint import load_checkpoint, list_saved_versions
from app.models.advanced_ml import AdvancedMLModel, AdvancedMLPrediction

logger = logging.getLogger(__name__)


class AutoencoderPredictor:
    """Predictor caching active model checkpoint in memory for ultra-fast CPU inference."""

    _cached_version: Optional[str] = None
    _cached_model: Optional[DocumentAutoencoder] = None
    _cached_scaler: Any = None
    _cached_metadata: Optional[Dict[str, Any]] = None
    _cached_schema: Optional[Dict[str, Any]] = None

    @classmethod
    def load(cls, version: Optional[str] = None) -> "AutoencoderPredictor":
        """Loads specific version or latest available version."""
        if version is None:
            available = list_saved_versions()
            if not available:
                raise FileNotFoundError("No trained Autoencoder models available in storage.")
            version = available[-1]

        if cls._cached_version != version:
            model, scaler, metadata, schema = load_checkpoint(version)
            cls._cached_version = version
            cls._cached_model = model
            cls._cached_scaler = scaler
            cls._cached_metadata = metadata
            cls._cached_schema = schema

        return cls()

    @property
    def model_version(self) -> str:
        return self._cached_version or "unknown"

    @property
    def input_mode(self) -> str:
        return (self._cached_metadata or {}).get("input_mode", "structured")

    @property
    def expected_dimension(self) -> int:
        return (self._cached_schema or {}).get("feature_dimension", 0)

    @property
    def threshold(self) -> float:
        return float((self._cached_metadata or {}).get("threshold", 0.05))

    def predict(
        self,
        features: np.ndarray,
        document_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Runs reconstruction error scoring.
        features: 1D array of length expected_dim or 2D array of shape (1, expected_dim).
        """
        if features.ndim == 1:
            features = features.reshape(1, -1)

        n_samples, dim = features.shape
        if dim != self.expected_dimension:
            raise ValueError(
                f"Feature dimension mismatch: expected {self.expected_dimension}, received {dim}"
            )

        # Scale features using frozen training scaler
        scaled = self._cached_scaler.transform(features)
        tensor = torch.tensor(scaled, dtype=torch.float32)

        # Compute MSE reconstruction errors
        errors = compute_reconstruction_errors(self._cached_model, tensor)
        rec_error = float(errors[0])

        # Score anomaly relative to threshold
        prediction, anomaly_score = score_anomaly(rec_error, self.threshold)

        result = {
            "model": "Autoencoder",
            "model_version": self.model_version,
            "reconstruction_error": round(rec_error, 6),
            "threshold": round(self.threshold, 6),
            "anomaly_score": round(anomaly_score, 4),
            "prediction": int(prediction),
            "input_mode": self.input_mode,
        }

        # Persist to advanced_ml_predictions if db provided
        if db is not None and document_id is not None:
            active_model = (
                db.query(AdvancedMLModel)
                .filter(AdvancedMLModel.model_version == self.model_version)
                .first()
            )
            model_id = active_model.id if active_model else None

            pred_record = AdvancedMLPrediction(
                document_id=document_id,
                model_id=model_id,
                model_name="Autoencoder",
                model_version=self.model_version,
                input_mode=self.input_mode,
                reconstruction_error=rec_error,
                anomaly_score=anomaly_score,
                threshold=self.threshold,
                prediction=prediction,
                prediction_metadata=result,
            )
            db.add(pred_record)
            db.commit()
            db.refresh(pred_record)
            result["prediction_id"] = pred_record.id

        return result
