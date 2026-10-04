"""
Pydantic schemas for Feature Engineering endpoints and dataset exports.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FeatureGenerationResponse(BaseModel):
    """Response returned when generating features for a document."""
    success: bool
    document_id: str
    feature_version: str
    feature_count: int
    status: str
    message: Optional[str] = None


class FeatureVectorResponse(BaseModel):
    """Response returned when retrieving a document's feature vector."""
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    feature_version: str
    pipeline_version: str
    feature_count: int
    feature_names: List[str]
    feature_values: List[Any]
    features: Dict[str, Any]
    normalized_features: Optional[Dict[str, float]] = None
    extraction_timestamp: str


class FeatureRegistryItem(BaseModel):
    name: str
    category: str
    datatype: str
    description: str
    source: str
    nullable: bool
    default_value: Any
    normalization: Optional[str] = None


class FeatureRegistryResponse(BaseModel):
    """Response detailing all available features in registry."""
    total_features: int
    features: List[FeatureRegistryItem]


class DatasetExportResponse(BaseModel):
    """Response returned when exporting dataset as JSON."""
    total_documents: int
    feature_version: str
    feature_names: List[str]
    records: List[Dict[str, Any]]
