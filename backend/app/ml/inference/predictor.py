"""
Inference Predictor Module.
Consumes Phase 3 feature vectors, transforms them with pre-fitted scalers,
computes raw decision scores and normalized anomaly scores, applies thresholding,
computes feature deviation explainability, and stores prediction history.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
from sqlalchemy.orm import Session

from app.ml.anomaly_detection.isolation_forest import IsolationForestDetector
from app.ml.anomaly_detection.scoring import AnomalyScorer
from app.ml.anomaly_detection.threshold import ThresholdManager
from app.ml.config import LEGAL_FORENSIC_DISCLAIMER
from app.ml.model_registry.registry import ModelRegistryService
from app.ml.preprocessing.feature_loader import FeatureLoader
from app.ml.schemas import (
    BatchPredictResponse,
    FeatureContributionSchema,
    PredictionResultSchema,
)
from app.models.document import Document
from app.models.document_features import DocumentFeatures
from app.models.ml_prediction import MLPrediction
from app.services.feature_engineering.feature_registry import FeatureRegistry


class AnomalyPredictor:
    """Handles anomaly scoring inference for documents."""

    def __init__(
        self,
        registry: Optional[FeatureRegistry] = None,
        registry_service: Optional[ModelRegistryService] = None,
    ):
        self.registry = registry or FeatureRegistry()
        self.registry_service = registry_service or ModelRegistryService()
        self.feature_loader = FeatureLoader(self.registry)
        self.scorer = AnomalyScorer(self.registry)
        self.detector: Optional[IsolationForestDetector] = None
        self.model_version: str = "1.0"

    def fit(self, X: np.ndarray) -> "AnomalyPredictor":
        """Fit or initialize detector with given features matrix."""
        if self.detector is None:
            self.detector = IsolationForestDetector()
        self.detector.fit(X)
        return self

    def predict(
        self,
        features: np.ndarray,
        feature_names: Optional[List[str]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Run inference directly on a feature vector (1D or 2D array).
        """
        if features.ndim == 1:
            x_2d = features.reshape(1, -1)
        else:
            x_2d = features

        if self.detector is None or not getattr(self.detector, "is_fitted", False):
            loaded = False
            if db is not None:
                try:
                    _, detector, _ = self.registry_service.load_active_artifacts(db)
                    self.detector = detector
                    loaded = True
                except Exception:
                    loaded = False
            if not loaded:
                self.detector = IsolationForestDetector()
                fit_data = np.repeat(x_2d, 10, axis=0) if len(x_2d) == 1 else x_2d
                self.detector.fit(fit_data)

        raw_score = float(self.detector.decision_function(x_2d)[0])
        anomaly_score = self.scorer.compute_anomaly_score(raw_score)
        prediction_val, status_str = self.scorer.determine_prediction(anomaly_score, threshold=0.50)

        return {
            "prediction": "anomaly" if prediction_val == 1 else "normal",
            "prediction_value": prediction_val,
            "anomaly_score": anomaly_score,
            "raw_score": raw_score,
            "status": status_str,
        }

    def predict_document(
        self,
        document_id: str,
        db: Session,
        model_name: str = "IsolationForest",
        custom_threshold: Optional[float] = None,
    ) -> PredictionResultSchema:
        """
        Run inference on a processed document:
        1. Verify document exists.
        2. Verify Phase 3 feature record exists.
        3. Load active model and pre-fitted scaler.
        4. Validate feature version compatibility.
        5. Transform features.
        6. Compute raw and normalized anomaly score.
        7. Compute explainable feature contributions.
        8. Store prediction record.
        """
        # 1. Check document
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise ValueError(f"Document with id '{document_id}' not found.")

        # 2. Check Phase 3 features
        features_record = (
            db.query(DocumentFeatures)
            .filter(DocumentFeatures.document_id == document_id)
            .first()
        )
        if not features_record:
            raise ValueError(
                f"Document '{document_id}' has not undergone feature engineering. "
                "Run Phase 3 feature generation via POST /api/documents/{id}/features first."
            )

        # 3. Load active model artifacts
        active_model, detector, scaler = self.registry_service.load_active_artifacts(
            db, model_name=model_name
        )

        # 4. Check feature version compatibility
        if features_record.feature_version != active_model.feature_version:
            raise ValueError(
                f"Feature version mismatch: document has version '{features_record.feature_version}', "
                f"but model '{active_model.model_version}' requires version '{active_model.feature_version}'."
            )

        # 5. Extract and align features
        feature_names: List[str] = active_model.feature_names_json
        features_dict: Dict[str, Any] = features_record.features_json

        x_raw = self.feature_loader.features_dict_to_array(features_dict, feature_names)
        x_2d = x_raw.reshape(1, -1)

        # 6. Transform using pre-fitted scaler (NO data leakage)
        x_scaled = scaler.transform(x_2d)

        # 7. Model decision score
        raw_score = float(detector.decision_function(x_scaled)[0])
        anomaly_score = self.scorer.compute_anomaly_score(raw_score)

        # 8. Thresholding
        threshold = custom_threshold if custom_threshold is not None else (active_model.configuration_json.get("threshold", 0.50) if isinstance(active_model.configuration_json, dict) else 0.50)
        prediction_val, status_str = self.scorer.determine_prediction(anomaly_score, threshold)

        # 9. Explainability: Contributing features
        baseline_stats = active_model.baseline_stats_json or {}
        contributing_features = self.scorer.compute_contributing_features(
            features_dict, baseline_stats
        )

        now = datetime.now(timezone.utc)

        # 10. Persist prediction record
        pred_record = MLPrediction(
            document_id=document_id,
            model_id=active_model.id,
            model_name=active_model.model_name,
            model_version=active_model.model_version,
            feature_version=active_model.feature_version,
            raw_score=raw_score,
            anomaly_score=anomaly_score,
            prediction=prediction_val,
            threshold=threshold,
            contributing_features_json=[cf.model_dump() for cf in contributing_features],
            prediction_timestamp=now,
            created_at=now,
        )
        db.add(pred_record)
        db.commit()
        db.refresh(pred_record)

        return PredictionResultSchema(
            document_id=document_id,
            model_id=active_model.id,
            model_name=active_model.model_name,
            model_version=active_model.model_version,
            feature_version=active_model.feature_version,
            raw_score=np.round(raw_score, 4),
            anomaly_score=anomaly_score,
            prediction=prediction_val,
            status=status_str,
            threshold=threshold,
            contributing_features=contributing_features,
            disclaimer=LEGAL_FORENSIC_DISCLAIMER,
            prediction_timestamp=now,
        )

    def predict_batch(
        self,
        document_ids: List[str],
        db: Session,
        model_name: str = "IsolationForest",
        custom_threshold: Optional[float] = None,
    ) -> BatchPredictResponse:
        """
        Process batch of documents. Tolerates individual document errors without
        aborting the entire batch.
        """
        results: List[PredictionResultSchema] = []
        errors: Dict[str, str] = {}

        for doc_id in document_ids:
            try:
                res = self.predict_document(
                    doc_id, db, model_name=model_name, custom_threshold=custom_threshold
                )
                results.append(res)
            except Exception as e:
                errors[doc_id] = str(e)

        return BatchPredictResponse(
            total_requested=len(document_ids),
            processed_count=len(results) + len(errors),
            success_count=len(results),
            failure_count=len(errors),
            results=results,
            errors=errors,
        )

    def get_document_predictions(
        self,
        document_id: str,
        db: Session,
    ) -> List[PredictionResultSchema]:
        """Fetch all historical predictions for a document, latest first."""
        records = (
            db.query(MLPrediction)
            .filter(MLPrediction.document_id == document_id)
            .order_by(MLPrediction.created_at.desc())
            .all()
        )
        results: List[PredictionResultSchema] = []
        for r in records:
            cf_list = []
            if r.contributing_features_json:
                cf_list = [
                    FeatureContributionSchema(**cf) for cf in r.contributing_features_json
                ]
            status_str = "anomalous" if r.prediction == 1 else "normal"
            results.append(
                PredictionResultSchema(
                    document_id=r.document_id,
                    model_id=r.model_id,
                    model_name=r.model_name,
                    model_version=r.model_version,
                    feature_version=r.feature_version,
                    raw_score=r.raw_score,
                    anomaly_score=r.anomaly_score,
                    prediction=r.prediction,
                    status=status_str,
                    threshold=r.threshold,
                    contributing_features=cf_list,
                    disclaimer=LEGAL_FORENSIC_DISCLAIMER,
                    prediction_timestamp=r.prediction_timestamp,
                )
            )
        return results
