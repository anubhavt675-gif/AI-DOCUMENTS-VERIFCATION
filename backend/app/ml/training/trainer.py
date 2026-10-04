"""
Model Trainer Pipeline.
Orchestrates data splitting, data leakage prevention, preprocessing fitting,
Isolation Forest training, baseline distribution calculation, evaluation metrics,
artifact serialization, and registry recording.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from sqlalchemy.orm import Session

from app.ml.anomaly_detection.isolation_forest import IsolationForestDetector
from app.ml.anomaly_detection.scoring import AnomalyScorer
from app.ml.anomaly_detection.threshold import ThresholdManager
from app.ml.config import (
    CURRENT_FEATURE_VERSION,
    CURRENT_PIPELINE_VERSION,
    DEFAULT_IFOREST_PARAMS,
    DEFAULT_MODEL_NAME,
    MODELS_DIR,
)
from app.ml.preprocessing.feature_loader import FeatureLoader
from app.ml.preprocessing.scaler import FeatureScalerWrapper
from app.ml.schemas import MLModelConfig, TrainModelRequest
from app.ml.training.dataset import DatasetManager
from app.ml.training.evaluation import ModelEvaluator
from app.ml.utils.serialization import save_artifact, save_json
from app.models.ml_model import MLModel
from app.services.feature_engineering.feature_registry import FeatureRegistry


class ModelTrainer:
    """End-to-end model training workflow manager."""

    def __init__(self, registry: Optional[FeatureRegistry] = None):
        self.registry = registry or FeatureRegistry()
        self.dataset_manager = DatasetManager(self.registry)
        self.feature_loader = FeatureLoader(self.registry)
        self.evaluator = ModelEvaluator()
        self.scorer = AnomalyScorer(self.registry)
        self.threshold_mgr = ThresholdManager()

    def train(
        self,
        db: Session,
        request: TrainModelRequest,
        dataset_records: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute full training pipeline.
        If dataset_records is None, loads existing records from document_features table.
        """
        # 1. Determine feature schema and order
        ordered_feature_names = self.registry.get_feature_names()
        feature_version = request.feature_version or CURRENT_FEATURE_VERSION

        # 2. Load dataset
        if dataset_records is None:
            dataset_records = self.dataset_manager.load_from_db(db, feature_version=feature_version)

        # 3. Model versioning
        model_name = request.model_name or DEFAULT_MODEL_NAME
        if request.model_version:
            model_version = request.model_version
        else:
            existing_count = db.query(MLModel).filter(MLModel.model_name == model_name).count()
            model_version = f"1.{existing_count}.0"

        # 4. Hyperparameter configuration
        params = dict(DEFAULT_IFOREST_PARAMS)
        if request.config:
            params.update(request.config.model_dump(exclude_unset=True))
        if request.contamination is not None:
            params["contamination"] = request.contamination

        # 5. Split dataset without data leakage
        split = self.dataset_manager.prepare_dataset(
            records=dataset_records,
            ordered_feature_names=ordered_feature_names,
            random_state=params.get("random_state", 42),
        )

        if len(split.X_train) == 0:
            raise ValueError(
                f"No feature records available for training model version '{model_version}'. "
                "Process documents to generate Phase 3 features first."
            )

        # 6. Fit Scaler ONLY on Training Split
        scaler = FeatureScalerWrapper()
        X_train_scaled = scaler.fit_transform(split.X_train)

        # 7. Train Isolation Forest Detector
        detector = IsolationForestDetector(**params)
        detector.fit(X_train_scaled)

        # 8. Compute Baseline Distribution Statistics (for Explainability)
        baseline_stats = self.feature_loader.compute_baseline_statistics(
            split.X_train, ordered_feature_names
        )

        # 9. Evaluate if labeled test data exists or was supplied in request
        metrics_dict: Optional[Dict[str, Any]] = None
        eval_records = request.labeled_evaluation_dataset

        if eval_records:
            # External labeled evaluation benchmark
            X_eval, _, y_eval = self.feature_loader.load_dataset_from_dicts(
                eval_records, ordered_feature_names
            )
            if y_eval is not None and len(y_eval) > 0:
                X_eval_scaled = scaler.transform(X_eval)
                eval_raw_scores = detector.decision_function(X_eval_scaled)
                eval_anomaly_scores = self.scorer.compute_batch_anomaly_scores(eval_raw_scores)
                eval_preds = self.threshold_mgr.classify(eval_anomaly_scores)
                metrics = self.evaluator.evaluate(y_eval, eval_preds, eval_anomaly_scores)
                metrics_dict = metrics.model_dump()
        elif split.y_test is not None and len(split.y_test) > 0:
            # Labeled test split from initial dataset
            X_test_scaled = scaler.transform(split.X_test)
            test_raw_scores = detector.decision_function(X_test_scaled)
            test_anomaly_scores = self.scorer.compute_batch_anomaly_scores(test_raw_scores)
            test_preds = self.threshold_mgr.classify(test_anomaly_scores)
            metrics = self.evaluator.evaluate(split.y_test, test_preds, test_anomaly_scores)
            metrics_dict = metrics.model_dump()

        # 10. Persist Model and Scaler Artifacts to Disk
        artifact_dir = MODELS_DIR / f"v{model_version}"
        artifact_dir.mkdir(parents=True, exist_ok=True)

        model_file = artifact_dir / "model.joblib"
        scaler_file = artifact_dir / "scaler.joblib"
        metadata_file = artifact_dir / "metadata.json"
        schema_file = artifact_dir / "feature_schema.json"

        save_artifact(detector.get_underlying_model(), model_file)
        save_artifact(scaler.get_underlying_scaler(), scaler_file)

        metadata = {
            "model_name": model_name,
            "model_version": model_version,
            "feature_version": feature_version,
            "pipeline_version": CURRENT_PIPELINE_VERSION,
            "training_samples": len(split.X_train),
            "configuration": params,
            "threshold": self.threshold_mgr.get_threshold(),
            "metrics": metrics_dict,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        save_json(metadata, metadata_file)
        save_json({
            "feature_names": ordered_feature_names,
            "feature_count": len(ordered_feature_names),
        }, schema_file)

        # 11. Database Registration
        if request.set_active:
            # Deactivate any currently active models for this model_name
            db.query(MLModel).filter(MLModel.model_name == model_name).update(
                {"is_active": False}
            )

        db_model = MLModel(
            model_name=model_name,
            model_version=model_version,
            feature_version=feature_version,
            model_type="isolation_forest",
            model_path=str(model_file),
            preprocessing_path=str(scaler_file),
            configuration_json=params,
            metrics_json=metrics_dict,
            feature_names_json=ordered_feature_names,
            baseline_stats_json=baseline_stats,
            is_active=request.set_active,
            training_sample_count=len(split.X_train),
            description=request.description or f"Trained on {len(split.X_train)} document feature records",
        )
        db.add(db_model)
        db.commit()
        db.refresh(db_model)

        return {
            "success": True,
            "model_id": db_model.id,
            "model_name": model_name,
            "model_version": model_version,
            "feature_version": feature_version,
            "training_samples": len(split.X_train),
            "is_active": db_model.is_active,
            "metrics": metrics_dict,
            "status": "completed",
        }
