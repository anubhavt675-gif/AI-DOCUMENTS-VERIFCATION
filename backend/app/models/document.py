"""
SQLAlchemy ORM model for the documents table.
Uses a portable UUID implementation (String column) that works with both
PostgreSQL and SQLite (for tests).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Enum as SAEnum
from sqlalchemy.orm import relationship

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_type = Column(String(120), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    status = Column(
        SAEnum(
            "uploaded", "processing", "verified", "suspicious", "failed",
            name="document_status_enum",
        ),
        nullable=False,
        default="uploaded",
    )
    processing_status = Column(String(255), nullable=True)

    # Document Fingerprint & File Location
    file_path = Column(String(500), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)
    hash_algorithm = Column(String(20), nullable=True, default="SHA-256")

    # Relationship to DocumentAnalysis (Phase 2)
    analysis = relationship(
        "DocumentAnalysis",
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Relationship to DocumentFeatures (Phase 3)
    features = relationship(
        "DocumentFeatures",
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Relationship to ML Predictions (Phase 4)
    predictions = relationship(
        "MLPrediction",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="desc(MLPrediction.created_at)",
    )

    # Integrated Integrity & Verification (Phase 5, 6, 7)
    integrity_status = Column(String(50), nullable=True, default="UNREGISTERED", index=True)
    current_ipfs_cid = Column(String(128), nullable=True, index=True)
    current_sha256 = Column(String(64), nullable=True, index=True)

    # Relationships to Advanced ML, Blockchain, and IPFS
    embeddings = relationship(
        "DocumentEmbedding",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="desc(DocumentEmbedding.created_at)",
    )
    advanced_predictions = relationship(
        "AdvancedMLPrediction",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="desc(AdvancedMLPrediction.created_at)",
    )
    blockchain_records = relationship(
        "BlockchainRecord",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="desc(BlockchainRecord.created_at)",
    )
    verifications = relationship(
        "IntegrityVerification",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="desc(IntegrityVerification.created_at)",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
