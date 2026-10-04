"""
SQLAlchemy ORM model for ml_predictions table.
Maintains prediction history for documents, tracking raw and normalized
anomaly scores, binary classification (normal/anomalous), thresholds,
and explainability feature contributions.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

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
        ForeignKey("ml_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_name = Column(String(100), nullable=False, default="IsolationForest")
    model_version = Column(String(50), nullable=False)
    feature_version = Column(String(20), nullable=False, default="1.0")
    
    # Anomaly Scores
    raw_score = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    prediction = Column(Integer, nullable=False)  # 0 = NORMAL, 1 = ANOMALOUS
    threshold = Column(Float, nullable=False, default=0.50)
    
    # Explainable Feature Contribution
    contributing_features_json = Column(JSON, nullable=True)

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

    document = relationship("Document", back_populates="predictions")
    model = relationship("MLModel", back_populates="predictions")
