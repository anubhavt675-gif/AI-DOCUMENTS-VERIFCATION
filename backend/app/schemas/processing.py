"""
Pydantic schemas for document preprocessing and analysis endpoints.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProcessResponse(BaseModel):
    """Response returned when triggering document preprocessing."""
    success: bool
    document_id: str
    processing_status: str  # "completed", "processing", "pending", "failed"
    message: Optional[str] = None


class FileAnalysisSummary(BaseModel):
    filename: str
    type: str
    size: int
    hash: Optional[str] = None
    hash_algorithm: Optional[str] = "SHA-256"


class TextAnalysisSummary(BaseModel):
    raw_text: Optional[str] = None
    cleaned_text: Optional[str] = None
    word_count: int = 0
    character_count: int = 0
    paragraph_count: int = 0


class OCRAnalysisSummary(BaseModel):
    used: bool = False
    status: str = "not_required"
    error_message: Optional[str] = None


class DocumentAnalysisResponse(BaseModel):
    """
    Standardized preprocessing analysis result schema matching Phase 2 specifications.
    """
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    file: FileAnalysisSummary
    text: TextAnalysisSummary
    metadata: Dict[str, Any] = Field(default_factory=dict)
    structure: Dict[str, Any] = Field(default_factory=dict)
    ocr: OCRAnalysisSummary
    processing_status: str
    processing_error: Optional[str] = None
