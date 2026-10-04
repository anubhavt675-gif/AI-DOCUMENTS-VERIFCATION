"""
Model Comparison Engine (Phase 5).
Compares Isolation Forest (Phase 4 baseline) and PyTorch Autoencoder (Phase 5 advanced ML)
on identical ground truth evaluation datasets.
Computes real comparative metrics: Accuracy, Precision, Recall, F1, Specificity, FPR, FNR,
Inference latency, and ROC/PR AUC.
"""
import time
from typing import Any, Dict, List, Optional
import numpy as np

from app.ml.advanced.evaluation.evaluator import compute_binary_metrics
from app.ml.inference.predictor import AnomalyPredictor as IsolationForestPredictor
from app.ml.advanced.autoencoder.predictor import AutoencoderPredictor


class ModelComparator:
    """Executes head-to-head comparison between Isolation Forest and Autoencoder."""

    def __init__(
        self,
        iforest_predictor: Optional[IsolationForestPredictor] = None,
        autoencoder_predictor: Optional[AutoencoderPredictor] = None,
    ):
        self.iforest = iforest_predictor or IsolationForestPredictor()
        try:
            self.autoencoder = autoencoder_predictor or AutoencoderPredictor.load()
        except Exception:
            self.autoencoder = None

    def compare_on_data(
        self,
        features: np.ndarray,
        ground_truth: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Runs both models on the evaluation feature matrix, compares metrics,
        and measures precise inference time.
        """
        n_samples = len(features)
        y_true = np.asarray(ground_truth, dtype=int)

        # 1. Isolation Forest Evaluation
        if hasattr(self.iforest, "detector"):
            if self.iforest.detector is None or not getattr(self.iforest.detector, "is_fitted", False):
                self.iforest.fit(features)
        elif hasattr(self.iforest, "fit") and not getattr(self.iforest, "is_fitted", False):
            self.iforest.fit(features)

        start_time = time.perf_counter()
        iforest_preds = []
        iforest_scores = []
        for i in range(n_samples):
            pred_res = self.iforest.predict(features[i], feature_names)
            # Isolation forest prediction: 'normal' -> 0, 'anomaly' -> 1
            is_anomaly = 1 if (pred_res.get("prediction") == "anomaly" or pred_res.get("prediction") == 1 or pred_res.get("prediction_value") == 1) else 0
            iforest_preds.append(is_anomaly)
            iforest_scores.append(float(pred_res.get("anomaly_score", 0.0)))
        iforest_latency = (time.perf_counter() - start_time) / max(1, n_samples)
        iforest_metrics = compute_binary_metrics(
            y_true, np.array(iforest_preds), np.array(iforest_scores)
        )
        iforest_metrics["avg_inference_latency_ms"] = round(iforest_latency * 1000, 3)

        # 2. PyTorch Autoencoder Evaluation
        autoencoder_metrics = None
        if self.autoencoder is not None:
            # Check if dimension matches
            ae_dim = self.autoencoder.expected_dimension
            if features.shape[1] == ae_dim:
                start_time = time.perf_counter()
                ae_preds = []
                ae_scores = []
                for i in range(n_samples):
                    res = self.autoencoder.predict(features[i])
                    ae_preds.append(int(res["prediction"]))
                    ae_scores.append(float(res["anomaly_score"]))
                ae_latency = (time.perf_counter() - start_time) / max(1, n_samples)
                autoencoder_metrics = compute_binary_metrics(
                    y_true, np.array(ae_preds), np.array(ae_scores)
                )
                autoencoder_metrics["avg_inference_latency_ms"] = round(ae_latency * 1000, 3)
                autoencoder_metrics["model_version"] = self.autoencoder.model_version
                autoencoder_metrics["input_mode"] = self.autoencoder.input_mode

        return {
            "sample_count": n_samples,
            "isolation_forest": {
                "model_name": "Isolation Forest (scikit-learn)",
                "model_version": getattr(self.iforest, "model_version", "1.0"),
                "metrics": iforest_metrics,
            },
            "autoencoder": {
                "model_name": "PyTorch Autoencoder",
                "model_version": self.autoencoder.model_version if self.autoencoder else "N/A",
                "metrics": autoencoder_metrics,
                "status": "evaluated" if autoencoder_metrics else "unavailable_or_dimension_mismatch",
            },
        }
