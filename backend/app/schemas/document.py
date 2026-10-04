"""
Pydantic schemas for document request / response serialization.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    original_filename: str
    file_type: str
    file_size: int


class DocumentCreate(DocumentBase):
    stored_filename: str
    document_id: str  # UUID as string


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: str
    original_filename: str
    file_type: str
    file_size: int
    upload_timestamp: datetime
    status: str
    processing_status: Optional[str] = None
    file_hash: Optional[str] = None
    hash_algorithm: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UploadResponse(BaseModel):
    success: bool
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    message: str = "Document uploaded successfully"


class DocumentListResponse(BaseModel):
    success: bool
    total: int
    documents: list[DocumentResponse]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
