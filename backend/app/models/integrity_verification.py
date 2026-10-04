"""
SQLAlchemy ORM model for integrity_verifications table (Integrated Verification).
Stores multi-signal technical evidence results combining ML anomaly detection,
IPFS content retrieval checks, and Hyperledger Fabric immutable hash comparisons.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


class IntegrityVerification(Base):
    __tablename__ = "integrity_verifications"

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
    ml_prediction_id = Column(String(36), nullable=True)
    blockchain_record_id = Column(String(36), nullable=True)
    ipfs_cid = Column(String(128), nullable=True)
    current_hash = Column(String(64), nullable=True)
    registered_hash = Column(String(64), nullable=True)
    hash_match = Column(Boolean, nullable=False, default=False)
    ipfs_match = Column(Boolean, nullable=False, default=False)
    blockchain_match = Column(Boolean, nullable=False, default=False)
    final_status = Column(String(50), nullable=False)  # VERIFIED_INTEGRITY, INTEGRITY_MISMATCH, ANOMALY_DETECTED, etc.
    verification_details_json = Column(JSON, nullable=False)
    verified_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    document = relationship("Document", back_populates="verifications")
