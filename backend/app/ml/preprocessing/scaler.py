"""
Feature Scaler Preprocessing Layer.
Wraps scikit-learn StandardScaler to ensure strict separation between
training and inference (preventing data leakage).
"""
from typing import Optional
import numpy as np
from app.ml.compat import StandardScaler


class FeatureScalerWrapper:
    """
    Standard scaler wrapper that strictly separates fit and transform phases.
    Ensures that test/inference samples are normalized strictly with parameters
    learned from the training distribution.
    """

    def __init__(self, with_mean: bool = True, with_std: bool = True):
        self.scaler = StandardScaler(with_mean=with_mean, with_std=with_std)
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray) -> "FeatureScalerWrapper":
        """Fit scaler parameters on training data ONLY."""
        self.scaler.fit(X)
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform data using fitted parameters."""
        if not self.is_fitted:
            raise RuntimeError("Cannot transform data before fitting the scaler on training data.")
        return self.scaler.transform(X)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit on training data and transform it."""
        self.fit(X)
        return self.transform(X)

    def get_underlying_scaler(self) -> StandardScaler:
        return self.scaler

    def set_underlying_scaler(self, scaler: StandardScaler) -> None:
        self.scaler = scaler
        self.is_fitted = True
