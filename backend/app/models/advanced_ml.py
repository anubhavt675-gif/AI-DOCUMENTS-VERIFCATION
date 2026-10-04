"""
SQLAlchemy ORM models for Advanced ML (Phase 5).
Tracks PyTorch Autoencoders, reconstruction error predictions,
and multi-model comparison benchmarks (Isolation Forest vs Autoencoder).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AdvancedMLModel(Base):
    __tablename__ = "advanced_ml_models"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    model_name = Column(String(100), nullable=False, default="PyTorchAutoencoder")
    model_version = Column(String(50), nullable=False, unique=True, index=True)
    model_type = Column(String(50), nullable=True, default="PyTorch-Autoencoder")
    feature_version = Column(String(20), nullable=False, default="1.0")
    embedding_version = Column(String(20), nullable=False, default="1.0")
    input_mode = Column(String(50), nullable=False, default="structured")  # 'structured' or 'structured_plus_text_embedding'
    input_dim = Column(Integer, nullable=True)
    input_dimension = Column(Integer, nullable=True)
    latent_dim = Column(Integer, nullable=True, default=16)
    model_path = Column(String(500), nullable=True)
    scaler_path = Column(String(500), nullable=True)
    artifact_path = Column(String(500), nullable=True)
    parameters = Column(JSON, nullable=True)
    configuration_json = Column(JSON, nullable=True)
    metrics_json = Column(JSON, nullable=True)
    training_metrics = Column(JSON, nullable=True)
    threshold = Column(Float, nullable=False, default=0.05)
    threshold_method = Column(String(50), nullable=False, default="percentile_95")
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    training_sample_count = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    predictions = relationship(
        "AdvancedMLPrediction",
        back_populates="model",
        cascade="all, delete-orphan",
    )


class AdvancedMLPrediction(Base):
    __tablename__ = "advanced_ml_predictions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    document_id = Column(
        String(36),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_id = Column(
        String(36),
        ForeignKey("advanced_ml_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_name = Column(String(100), nullable=False, default="PyTorchAutoencoder")
    model_version = Column(String(50), nullable=False)
    input_mode = Column(String(50), nullable=False, default="structured")
    reconstruction_error = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)  # Normalized [0.0, 1.0]
    prediction = Column(Integer, nullable=False)   # 0 = NORMAL, 1 = ANOMALOUS
    threshold = Column(Float, nullable=False)
    prediction_metadata = Column(JSON, nullable=True)
    prediction_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    document = relationship("Document", back_populates="advanced_predictions")
    model = relationship("AdvancedMLModel", back_populates="predictions")


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    experiment_id = Column(String(100), nullable=False, index=True)
    baseline_model_id = Column(String(36), nullable=True)
    advanced_model_id = Column(String(36), nullable=True)
    dataset_version = Column(String(50), nullable=False, default="benchmark_v1")
    comparison_metrics_json = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
