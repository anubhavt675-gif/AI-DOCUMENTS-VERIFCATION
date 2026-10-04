"""
Exceptions for feature engineering pipeline.
"""

class FeatureEngineeringError(Exception):
    """Base exception for all feature engineering errors."""
    pass


class PreprocessingIncompleteError(FeatureEngineeringError):
    """Raised when attempting feature extraction on an unprocessed or failed document."""
    pass


class InvalidFeatureVectorError(FeatureEngineeringError):
    """Raised when generated feature vector contains NaN, Inf, or violates schema."""
    pass


FeatureValidationError = InvalidFeatureVectorError


class FeatureRegistryError(FeatureEngineeringError):
    """Raised when a feature name is unregistered or has mismatched specifications."""
    pass
