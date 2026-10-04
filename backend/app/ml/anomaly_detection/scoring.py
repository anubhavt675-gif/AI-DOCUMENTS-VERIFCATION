"""
Anomaly Scoring and Explainability Engine.
Transforms raw decision function scores into normalized, human-interpretable
anomaly scores [0.0, 1.0] and computes feature deviation from baseline distributions.
"""
from typing import Any, Dict, List, Optional
import numpy as np

from app.ml.config import (
    LABEL_ANOMALOUS,
    LABEL_NORMAL,
    STATUS_ANOMALOUS,
    STATUS_NORMAL,
    TOP_CONTRIBUTING_FEATURES_COUNT,
)
from app.ml.schemas import FeatureContributionSchema
from app.services.feature_engineering.feature_registry import FeatureRegistry


class AnomalyScorer:
    """
    Computes calibrated anomaly scores and explains deviations from baseline distribution.
    """

    def __init__(self, registry: Optional[FeatureRegistry] = None, alpha: float = 10.0):
        self.registry = registry or FeatureRegistry()
        self.alpha = alpha  # Sigmoid steepness parameter

    def compute_anomaly_score(self, raw_score: float) -> float:
        """
        Convert raw Isolation Forest decision score into normalized anomaly score in [0.0, 1.0].
        - raw_score == 0.0 -> anomaly_score == 0.50 (exact decision boundary)
        - raw_score > 0.0  -> anomaly_score < 0.50 (inlier / normal document)
        - raw_score < 0.0  -> anomaly_score > 0.50 (outlier / statistical anomaly)
        """
        # Clamp to avoid overflow in exp
        val = np.clip(self.alpha * raw_score, -50.0, 50.0)
        prob = 1.0 / (1.0 + np.exp(val))
        return float(np.round(prob, 4))

    def compute_batch_anomaly_scores(self, raw_scores: np.ndarray) -> np.ndarray:
        """Vectorized computation of anomaly scores from raw scores."""
        vals = np.clip(self.alpha * raw_scores, -50.0, 50.0)
        probs = 1.0 / (1.0 + np.exp(vals))
        return np.round(probs, 4)

    def determine_prediction(
        self,
        anomaly_score: float,
        threshold: float = 0.50,
    ) -> tuple[int, str]:
        """
        Determine classification label and status string.
        Returns:
            (prediction_label, status_string)
            e.g. (0, 'normal') or (1, 'anomalous')
        """
        if anomaly_score >= threshold:
            return LABEL_ANOMALOUS, STATUS_ANOMALOUS
        return LABEL_NORMAL, STATUS_NORMAL

    def compute_contributing_features(
        self,
        features_dict: Dict[str, Any],
        baseline_stats: Dict[str, Dict[str, float]],
        top_k: int = TOP_CONTRIBUTING_FEATURES_COUNT,
    ) -> List[FeatureContributionSchema]:
        """
        Explainability: Identify features that deviate the most from the training distribution.
        Does NOT claim tampering; identifies statistical shifts from the baseline.
        """
        if not baseline_stats:
            return []

        deviations: List[dict] = []
        for name, stats in baseline_stats.items():
            if name not in features_dict:
                continue

            val = features_dict[name]
            if isinstance(val, bool):
                num_val = 1.0 if val else 0.0
            else:
                try:
                    num_val = float(val)
                except (ValueError, TypeError):
                    continue

            mean = stats.get("mean", 0.0)
            std = stats.get("std", 1.0)
            if std <= 1e-7:
                std = 1.0

            # Z-score deviation
            z_score = abs(num_val - mean) / std

            # Only consider meaningful deviations
            if z_score > 0.01:
                desc = None
                try:
                    f_def = self.registry.get(name)
                    desc = f_def.description
                except Exception:
                    pass

                deviations.append({
                    "feature_name": name,
                    "document_value": float(np.round(num_val, 4)),
                    "baseline_mean": float(np.round(mean, 4)),
                    "baseline_std": float(np.round(std, 4)),
                    "deviation_score": float(np.round(z_score, 3)),
                    "description": desc,
                })

        # Sort descending by deviation score
        deviations.sort(key=lambda x: x["deviation_score"], reverse=True)

        return [
            FeatureContributionSchema(**d)
            for d in deviations[:top_k]
        ]
