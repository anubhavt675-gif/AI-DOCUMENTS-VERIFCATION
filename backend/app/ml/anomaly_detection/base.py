"""
Abstract Base Class for Anomaly Detectors.
Defines common interface so future models (PyTorch Autoencoders, One-Class SVM)
can be swapped seamlessly without altering the rest of the pipeline.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
import numpy as np


class BaseAnomalyDetector(ABC):
    """Abstract interface for all document anomaly detection models."""

    @abstractmethod
    def fit(self, X: np.ndarray) -> "BaseAnomalyDetector":
        """Fit model on training feature matrix X (unsupervised)."""
        pass

    @abstractmethod
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Compute raw anomaly/inlier decision function scores.
        Convention: higher scores indicate more normal; lower/negative indicate anomalous.
        """
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict binary labels:
        0 = Normal
        1 = Anomalous
        """
        pass

    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """Return model parameters."""
        pass
