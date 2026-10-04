"""
SQLAlchemy ORM model for document_analysis table.
Stores extracted text, metadata, structural data, and OCR status.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentAnalysis(Base):
    __tablename__ = "document_analysis"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        String(36),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    raw_text = Column(Text, nullable=True)
    cleaned_text = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=False, default=0)
    character_count = Column(Integer, nullable=False, default=0)
    page_count = Column(Integer, nullable=False, default=0)
    image_count = Column(Integer, nullable=False, default=0)
    table_count = Column(Integer, nullable=False, default=0)
    paragraph_count = Column(Integer, nullable=False, default=0)
    metadata_json = Column(JSON, nullable=True)
    structural_data_json = Column(JSON, nullable=True)
    ocr_used = Column(Boolean, nullable=False, default=False)
    ocr_status = Column(String(50), nullable=False, default="not_required")
    processing_error = Column(Text, nullable=True)

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

    document = relationship("Document", back_populates="analysis")
