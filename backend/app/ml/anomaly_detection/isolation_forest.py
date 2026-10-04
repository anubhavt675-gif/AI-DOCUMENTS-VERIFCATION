"""
Isolation Forest Anomaly Detector.
Wraps scikit-learn IsolationForest to adhere to project standards:
- Internal labels: 0 = NORMAL, 1 = ANOMALOUS (scikit-learn uses 1 for inlier, -1 for outlier).
- Unsupervised training.
- Reproducible random state.
"""
from typing import Any, Dict, Optional
import numpy as np
from app.ml.compat import IsolationForest

from app.ml.anomaly_detection.base import BaseAnomalyDetector
from app.ml.config import DEFAULT_IFOREST_PARAMS, LABEL_ANOMALOUS, LABEL_NORMAL


class IsolationForestDetector(BaseAnomalyDetector):
    """
    Scikit-learn Isolation Forest model adapter.
    Identifies anomalous document patterns through tree partitioning depth.
    """

    def __init__(self, **params):
        merged_params = dict(DEFAULT_IFOREST_PARAMS)
        merged_params.update(params)
        self.params = merged_params
        self.model = IsolationForest(**self.params)
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray) -> "IsolationForestDetector":
        """Fit Isolation Forest on feature matrix X."""
        self.model.fit(X)
        self.is_fitted = True
        return self

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Compute decision function.
        scikit-learn decision_function returns negative values for outliers,
        positive for inliers.
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() before decision_function().")
        return self.model.decision_function(X)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Compute the raw negative anomaly score.
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() before score_samples().")
        return self.model.score_samples(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict project-standard labels:
        0 = Normal
        1 = Anomalous
        (Maps scikit-learn's 1 -> 0, and -1 -> 1)
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() before predict().")
        raw_preds = self.model.predict(X)
        # scikit-learn: 1 is inlier (normal), -1 is outlier (anomalous)
        return np.where(raw_preds == -1, LABEL_ANOMALOUS, LABEL_NORMAL)

    def get_params(self) -> Dict[str, Any]:
        """Return configuration dictionary."""
        return dict(self.params)

    def get_underlying_model(self) -> IsolationForest:
        """Access the wrapped scikit-learn model."""
        return self.model

    def set_underlying_model(self, model: IsolationForest) -> None:
        """Set pre-trained scikit-learn model."""
        self.model = model
        self.is_fitted = True
