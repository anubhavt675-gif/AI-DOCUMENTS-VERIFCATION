"""
SQLAlchemy ORM model for ml_models table.
Tracks registered machine learning models, versions, types, paths,
hyperparameters, evaluation metrics, and active production status.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    model_name = Column(String(100), nullable=False, default="IsolationForest")
    model_version = Column(String(50), nullable=False, unique=True, index=True)
    feature_version = Column(String(20), nullable=False, default="1.0")
    model_type = Column(String(50), nullable=False, default="isolation_forest")
    model_path = Column(String(500), nullable=False)
    preprocessing_path = Column(String(500), nullable=False)
    configuration_json = Column(JSON, nullable=False)
    metrics_json = Column(JSON, nullable=True)
    feature_names_json = Column(JSON, nullable=False)
    baseline_stats_json = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    training_sample_count = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    predictions = relationship(
        "MLPrediction",
        back_populates="model",
        cascade="all, delete-orphan",
    )
