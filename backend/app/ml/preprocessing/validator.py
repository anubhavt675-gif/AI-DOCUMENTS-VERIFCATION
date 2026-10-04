"""
Feature Validator for Machine Learning.
Verifies that feature vectors conform to the expected schema, contain
no NaN or infinite values, and maintain valid numerical types.
"""
from typing import Any, Dict, List, Optional
import numpy as np

from app.services.feature_engineering.feature_registry import FeatureRegistry
from app.services.feature_engineering.exceptions import FeatureValidationError


class FeatureValidator:
    """Validates features before training and inference."""

    def __init__(self, registry: Optional[FeatureRegistry] = None):
        self.registry = registry or FeatureRegistry()

    def validate_features_dict(
        self,
        features: Dict[str, Any],
        expected_feature_names: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Validate a dictionary of features:
        - Check that expected features are present (impute defaults if missing).
        - Ensure values are numeric.
        - Check for NaN or Inf.
        Returns a clean dictionary of float values.
        """
        target_keys = expected_feature_names or self.registry.get_feature_names()
        cleaned: Dict[str, float] = {}

        for key in target_keys:
            val = features.get(key)
            if val is None:
                # Use default value from registry
                try:
                    f_def = self.registry.get(key)
                    val = f_def.default_value
                except Exception:
                    val = 0.0

            # Convert boolean to float
            if isinstance(val, bool):
                val = 1.0 if val else 0.0

            # Convert numeric types
            try:
                num_val = float(val)
            except (ValueError, TypeError):
                raise FeatureValidationError(
                    f"Feature '{key}' has invalid non-numeric value: {val!r}"
                )

            # Check for NaN or Inf
            if np.isnan(num_val):
                raise FeatureValidationError(f"Feature '{key}' contains NaN")
            if np.isinf(num_val):
                raise FeatureValidationError(f"Feature '{key}' contains infinity")

            cleaned[key] = num_val

        return cleaned

    def validate_matrix(self, X: np.ndarray, expected_dim: Optional[int] = None) -> np.ndarray:
        """
        Validate 2D feature matrix:
        - Must be 2D numpy array.
        - No NaN or Inf.
        - Correct feature dimension.
        """
        if not isinstance(X, np.ndarray):
            X = np.asarray(X, dtype=np.float64)

        if X.ndim != 2:
            raise FeatureValidationError(f"Expected 2D array, got {X.ndim}D array with shape {X.shape}")

        if expected_dim is not None and X.shape[1] != expected_dim:
            raise FeatureValidationError(
                f"Feature dimension mismatch: expected {expected_dim}, got {X.shape[1]}"
            )

        if np.isnan(X).any():
            raise FeatureValidationError("Feature matrix contains NaN values")

        if np.isinf(X).any():
            raise FeatureValidationError("Feature matrix contains infinite values")

        return X
