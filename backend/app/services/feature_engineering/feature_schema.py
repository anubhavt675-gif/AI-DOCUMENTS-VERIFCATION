"""
Feature schema definitions and data representations for ML features.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class FeatureDefinition:
    """
    Formal specification for a single engineered feature in the registry.
    """
    name: str
    category: str  # 'file', 'text', 'text_quality', 'date_numeric', 'metadata', 'metadata_consistency', 'structural', 'image', 'cross_source', 'integrity'
    datatype: str  # 'integer', 'float', 'boolean', 'string'
    description: str
    source: str    # e.g., 'file_metadata', 'clean_text', 'structural_analyzer'
    nullable: bool = False
    default_value: Any = 0
    normalization: Optional[str] = "minmax"  # 'standard', 'minmax', None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeatureVector:
    """
    Complete, ordered, versioned feature vector produced for a document.
    """
    document_id: str
    feature_version: str = "1.0"
    pipeline_version: str = "1.0.0"
    features: Dict[str, Any] = field(default_factory=dict)
    feature_names: List[str] = field(default_factory=list)
    feature_values: List[Any] = field(default_factory=list)
    normalized_features: Optional[Dict[str, float]] = None
    extraction_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "feature_version": self.feature_version,
            "pipeline_version": self.pipeline_version,
            "features": self.features,
            "feature_names": self.feature_names,
            "feature_values": self.feature_values,
            "normalized_features": self.normalized_features,
            "extraction_timestamp": self.extraction_timestamp,
        }
