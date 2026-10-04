"""
SQLAlchemy ORM model for document_features table.
Stores extracted feature vectors, feature names, normalized feature representations,
and feature engineering version metadata.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentFeatures(Base):
    __tablename__ = "document_features"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        String(36),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    feature_version = Column(String(20), nullable=False, default="1.0")
    pipeline_version = Column(String(20), nullable=False, default="1.0.0")
    features_json = Column(JSON, nullable=True, default=dict)
    feature_names_json = Column(JSON, nullable=True, default=list)
    normalized_features_json = Column(JSON, nullable=True)
    feature_dimension = Column(Integer, nullable=True)
    feature_vector = Column(JSON, nullable=True)

    extraction_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    document = relationship("Document", back_populates="features")
