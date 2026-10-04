"""
Pydantic schemas for Machine Learning (Phase 4).
Covers training configuration, evaluation metrics, prediction inputs/outputs,
explainable feature contributions, batch requests, and monitoring statistics.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class MLModelConfig(BaseModel):
    """Hyperparameter configuration for Isolation Forest."""
    n_estimators: int = Field(default=300, ge=10, le=2000, description="Number of isolation trees")
    max_samples: Union[int, float, str] = Field(default="auto", description="Number of samples to draw to train each base estimator")
    contamination: Union[float, str] = Field(default="auto", description="'auto' or float proportion of outliers (0.0 to 0.5)")
    max_features: float = Field(default=1.0, gt=0.0, le=1.0, description="Proportion of features drawn to train each base estimator")
    bootstrap: bool = Field(default=False, description="Whether samples are drawn with replacement")
    random_state: int = Field(default=42, description="Random seed for reproducibility")


class TrainModelRequest(BaseModel):
    """Payload for training or retraining an anomaly detection model."""
    model_name: str = Field(default="IsolationForest", description="Name of the model architecture")
    model_version: Optional[str] = Field(default=None, description="Explicit version string (e.g. '1.0.1'); generated if omitted")
    feature_version: str = Field(default="1.0", description="Expected Phase 3 feature version")
    config: Optional[MLModelConfig] = Field(default=None, description="Custom model hyperparameters")
    contamination: Optional[Union[float, str]] = Field(default=None, description="Shortcut override for contamination parameter")
    set_active: bool = Field(default=True, description="Whether to activate this model for production inference upon completion")
    description: Optional[str] = Field(default=None, description="Description or release notes for this model version")
    
    # Optional labeled evaluation benchmark dataset for computing precision/recall/F1 without data leakage
    # Each item: {"document_id": "...", "features": {...}, "label": 0 or 1}
    labeled_evaluation_dataset: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional labeled dataset solely for validation/test evaluation metrics. Never used to train IsolationForest."
    )


class ConfusionMatrixSchema(BaseModel):
    tn: int = Field(..., description="True Negatives (Normal correctly identified as Normal)")
    fp: int = Field(..., description="False Positives (Normal falsely flagged as Anomalous)")
    fn: int = Field(..., description="False Negatives (Anomalous missed as Normal)")
    tp: int = Field(..., description="True Positives (Anomalous correctly identified as Anomalous)")


class EvaluationMetricsSchema(BaseModel):
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    accuracy: Optional[float] = None
    specificity: Optional[float] = None
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None
    roc_auc: Optional[float] = None
    average_precision: Optional[float] = None
    sample_count: int = 0
    normal_count: int = 0
    anomalous_count: int = 0
    confusion_matrix: Optional[ConfusionMatrixSchema] = None


class MLModelResponse(BaseModel):
    id: str
    model_name: str
    model_version: str
    feature_version: str
    model_type: str
    is_active: bool
    training_sample_count: int
    configuration: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    feature_names: List[str]
    description: Optional[str] = None
    created_at: datetime


class FeatureContributionSchema(BaseModel):
    """Explainability: Feature differing substantially from the training distribution."""
    feature_name: str
    document_value: float
    baseline_mean: float
    baseline_std: float
    deviation_score: float = Field(..., description="Z-score distance from training baseline distribution")
    description: Optional[str] = None


class PredictionResultSchema(BaseModel):
    """Result of running anomaly detection inference on a document."""
    document_id: str
    model_id: Optional[str] = None
    model_name: str
    model_version: str
    feature_version: str
    raw_score: float
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Normalized score: 0.0 = completely normal, 1.0 = highly anomalous")
    prediction: int = Field(..., description="0 = NORMAL, 1 = ANOMALOUS")
    status: str = Field(..., description="'normal' or 'anomalous'")
    threshold: float = Field(default=0.50)
    contributing_features: List[FeatureContributionSchema] = Field(default_factory=list)
    disclaimer: str
    prediction_timestamp: datetime


class BatchPredictRequest(BaseModel):
    document_ids: List[str] = Field(..., min_length=1, description="List of document IDs to evaluate")


class BatchPredictResponse(BaseModel):
    total_requested: int
    processed_count: int
    success_count: int
    failure_count: int
    results: List[PredictionResultSchema]
    errors: Dict[str, str] = Field(default_factory=dict)


class MLMonitoringStatsResponse(BaseModel):
    total_predictions: int
    normal_count: int
    anomalous_count: int
    anomaly_ratio: float
    average_anomaly_score: float
    model_breakdown: Dict[str, int]
    active_model: Optional[Dict[str, Any]] = None
