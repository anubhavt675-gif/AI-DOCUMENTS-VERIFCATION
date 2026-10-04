"""
Threshold Management Module.
Handles anomaly decision boundaries and supports optional threshold calibration
on labeled validation splits without data leakage.
"""
from typing import List, Tuple
import numpy as np
from app.ml.compat import f1_score

from app.ml.config import DEFAULT_ANOMALY_THRESHOLD, LABEL_ANOMALOUS, LABEL_NORMAL


class ThresholdManager:
    """Manages classification decision thresholds."""

    def __init__(self, default_threshold: float = DEFAULT_ANOMALY_THRESHOLD):
        self.threshold = default_threshold

    def get_threshold(self) -> float:
        return self.threshold

    def set_threshold(self, threshold: float) -> None:
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")
        self.threshold = threshold

    def classify(self, anomaly_scores: np.ndarray, threshold: float = None) -> np.ndarray:
        """Apply threshold to produce binary predictions."""
        thresh = threshold if threshold is not None else self.threshold
        return np.where(anomaly_scores >= thresh, LABEL_ANOMALOUS, LABEL_NORMAL)

    def calibrate_on_validation_set(
        self,
        val_anomaly_scores: np.ndarray,
        val_ground_truth: np.ndarray,
        candidate_thresholds: List[float] = None,
    ) -> Tuple[float, float]:
        """
        Tune threshold strictly on validation predictions and labels to maximize F1-score.
        Does NOT access test data.
        Returns:
            (best_threshold, best_f1)
        """
        if candidate_thresholds is None:
            candidate_thresholds = list(np.arange(0.20, 0.85, 0.05))

        best_thresh = self.threshold
        best_f1 = -1.0

        for thresh in candidate_thresholds:
            preds = np.where(val_anomaly_scores >= thresh, LABEL_ANOMALOUS, LABEL_NORMAL)
            score = float(f1_score(val_ground_truth, preds, zero_division=0))
            if score > best_f1:
                best_f1 = score
                best_thresh = float(thresh)

        if best_f1 > 0:
            self.threshold = best_thresh

        return self.threshold, best_f1
