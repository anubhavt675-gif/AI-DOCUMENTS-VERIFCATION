"""
SQLAlchemy ORM model for document_embeddings table (Phase 5).
Stores dense NLP semantic embeddings generated from chunked document text,
along with chunk metadata, aggregation method, and source text hash.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

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
    embedding_model = Column(String(100), nullable=False, default="all-MiniLM-L6-v2")
    embedding_version = Column(String(20), nullable=False, default="1.0")
    source_text_version = Column(String(64), nullable=False, index=True)
    embedding_dimension = Column(Integer, nullable=False, default=64)
    chunk_count = Column(Integer, nullable=False, default=1)
    aggregation_method = Column(String(50), nullable=False, default="mean")
    
    # Serialized float vector
    embedding_vector = Column(JSON, nullable=False)

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

    document = relationship("Document", back_populates="embeddings")
