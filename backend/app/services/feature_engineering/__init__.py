"""
Feature engineering module for the Official Government Document Anomaly Detection System.
"""
from app.services.feature_engineering.exceptions import (
    FeatureEngineeringError,
    FeatureRegistryError,
    InvalidFeatureVectorError,
    PreprocessingIncompleteError,
)
from app.services.feature_engineering.feature_registry import (
    FeatureRegistry,
    feature_registry,
)
from app.services.feature_engineering.feature_schema import (
    FeatureDefinition,
    FeatureVector,
)
from app.services.feature_engineering.normalization import (
    BaseFeatureScaler,
    MinMaxScaler,
    StandardScaler,
)
from app.services.feature_engineering.pipeline import (
    FEATURE_VERSION,
    PIPELINE_VERSION,
    FeatureEngineeringPipeline,
    default_pipeline,
)

__all__ = [
    "FeatureEngineeringError",
    "PreprocessingIncompleteError",
    "InvalidFeatureVectorError",
    "FeatureRegistryError",
    "FeatureDefinition",
    "FeatureVector",
    "FeatureRegistry",
    "feature_registry",
    "BaseFeatureScaler",
    "StandardScaler",
    "MinMaxScaler",
    "FeatureEngineeringPipeline",
    "default_pipeline",
    "FEATURE_VERSION",
    "PIPELINE_VERSION",
]
