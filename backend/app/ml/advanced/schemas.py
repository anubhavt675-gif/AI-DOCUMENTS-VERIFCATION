"""
Pydantic schemas for Phase 5 Advanced Machine Learning.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AutoencoderConfigSchema(BaseModel):
    hidden_dims: List[int] = Field(default=[64, 32], description="Encoder/decoder hidden layers")
    latent_dim: int = Field(default=16, description="Bottleneck representation dimension")
    learning_rate: float = Field(default=0.001, gt=0.0)
    batch_size: int = Field(default=16, ge=1)
    epochs: int = Field(default=40, ge=1, le=500)
    weight_decay: float = Field(default=1e-5)
    threshold_percentile: float = Field(default=95.0, ge=50.0, le=99.9)


class TrainAutoencoderRequest(BaseModel):
    model_name: str = Field(default="PyTorchAutoencoder")
    model_version: Optional[str] = None
    input_mode: str = Field(default="structured", description="'structured' or 'structured_plus_text_embedding'")
    config: Optional[AutoencoderConfigSchema] = None
    set_active: bool = True
    description: Optional[str] = None
    labeled_evaluation_dataset: Optional[List[Dict[str, Any]]] = None


class AdvancedTrainRequest(BaseModel):
    model_version: str = "1.0.0"
    input_mode: str = "structured"
    learning_rate: float = 0.001
    batch_size: int = 16
    epochs: int = 30
    latent_dim: int = 16
    threshold_method: str = "percentile"
    threshold_percentile: float = 95.0


class AdvancedTrainResponse(BaseModel):
    success: bool = True
    model_version: str
    input_mode: str
    input_dimension: int
    threshold: float
    training_duration_seconds: float
    artifact_path: str
    db_id: Optional[str] = None


class AdvancedPredictRequest(BaseModel):
    input_mode: Optional[str] = None


class AdvancedPredictResponse(BaseModel):
    model: str = "Autoencoder"
    model_version: str
    reconstruction_error: float
    threshold: float
    anomaly_score: float
    prediction: int = Field(..., description="0 = NORMAL, 1 = ANOMALOUS")
    input_mode: str
    prediction_id: Optional[str] = None


class AdvancedMLModelResponse(BaseModel):
    id: str
    model_name: str
    model_version: str
    feature_version: str
    embedding_version: str
    input_mode: str
    input_dim: int
    latent_dim: int
    threshold: float
    threshold_method: str
    is_active: bool
    training_sample_count: int
    configuration: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    created_at: datetime


class AutoencoderPredictionResponse(BaseModel):
    document_id: str
    model_name: str
    model_version: str
    input_mode: str
    reconstruction_error: float
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    prediction: int = Field(..., description="0 = NORMAL, 1 = ANOMALOUS")
    status: str = Field(..., description="'normal' or 'anomalous'")
    threshold: float
    disclaimer: str
    prediction_timestamp: datetime


class EmbeddingResponse(BaseModel):
    document_id: str
    embedding_model: str
    embedding_version: str
    embedding_dimension: int
    chunk_count: int
    aggregation_method: str
    source_text_version: str
    created_at: datetime


class ModelMetricsComparison(BaseModel):
    model_name: str
    model_version: str
    architecture: str
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    accuracy: Optional[float] = None
    specificity: Optional[float] = None
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None
    roc_auc: Optional[float] = None
    training_time_seconds: float
    inference_time_ms: float


class ModelComparisonResponse(BaseModel):
    experiment_id: str
    evaluated_samples: int
    dataset_version: str
    baseline_model: ModelMetricsComparison
    advanced_model: ModelMetricsComparison
    analysis_notes: str
    created_at: datetime
