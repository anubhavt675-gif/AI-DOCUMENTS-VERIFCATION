"""
Lightweight Model Registry Service.
Tracks registered machine learning models, handles version switching,
and caches active model artifacts in memory to prevent repetitive disk I/O.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.ml.compat import IsolationForest, StandardScaler

from app.ml.anomaly_detection.isolation_forest import IsolationForestDetector
from app.ml.preprocessing.scaler import FeatureScalerWrapper
from app.ml.utils.serialization import load_artifact
from app.models.ml_model import MLModel


class ModelRegistryService:
    """Service for managing model lifecycles and cached runtime instances."""

    def __init__(self):
        # In-memory artifact cache: {model_id: (IsolationForestDetector, FeatureScalerWrapper)}
        self._artifact_cache: Dict[str, Tuple[IsolationForestDetector, FeatureScalerWrapper]] = {}

    def clear_cache(self) -> None:
        """Clear memory cache of loaded model artifacts."""
        self._artifact_cache.clear()

    def list_models(self, db: Session) -> List[MLModel]:
        """List all registered models ordered by newest first."""
        return db.query(MLModel).order_by(MLModel.created_at.desc()).all()

    def get_model_by_id(self, model_id: str, db: Session) -> Optional[MLModel]:
        """Fetch model by primary key."""
        return db.query(MLModel).filter(MLModel.id == model_id).first()

    def get_model_by_version(self, version: str, db: Session) -> Optional[MLModel]:
        """Fetch model by version string."""
        return db.query(MLModel).filter(MLModel.model_version == version).first()

    def get_active_model(self, db: Session, model_name: str = "IsolationForest") -> Optional[MLModel]:
        """Fetch the currently active model record for production inference."""
        return (
            db.query(MLModel)
            .filter(MLModel.model_name == model_name, MLModel.is_active == True)
            .first()
        )

    def activate_model(self, model_id: str, db: Session) -> MLModel:
        """Set specified model as active and deactivate all other versions."""
        model = self.get_model_by_id(model_id, db)
        if not model:
            raise ValueError(f"Model with id '{model_id}' does not exist.")

        # Deactivate all other versions of this model_name
        db.query(MLModel).filter(MLModel.model_name == model.model_name).update(
            {"is_active": False}
        )

        model.is_active = True
        db.commit()
        db.refresh(model)
        return model

    def load_active_artifacts(
        self, db: Session, model_name: str = "IsolationForest"
    ) -> Tuple[MLModel, IsolationForestDetector, FeatureScalerWrapper]:
        """
        Load or retrieve cached model and scaler for the active model.
        Returns:
            (model_db_record, detector_instance, scaler_instance)
        """
        active_record = self.get_active_model(db, model_name=model_name)
        if not active_record:
            raise RuntimeError(
                f"No active ML model found for '{model_name}'. Train a model first via /api/ml/train."
            )

        if active_record.id in self._artifact_cache:
            detector, scaler = self._artifact_cache[active_record.id]
            return active_record, detector, scaler

        # Load from disk
        model_path = Path(active_record.model_path)
        scaler_path = Path(active_record.preprocessing_path)

        underlying_model = load_artifact(model_path)
        underlying_scaler = load_artifact(scaler_path)

        detector = IsolationForestDetector()
        detector.set_underlying_model(underlying_model)

        scaler = FeatureScalerWrapper()
        scaler.set_underlying_scaler(underlying_scaler)

        # Cache in memory
        self._artifact_cache[active_record.id] = (detector, scaler)
        return active_record, detector, scaler
