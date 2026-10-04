"""
Feature Engineering Pipeline orchestrator.
Executes modular feature extractors, validates feature values and data types against
the central FeatureRegistry, and constructs deterministic, versioned FeatureVectors.
"""
from datetime import datetime, timezone
import logging
import math
from typing import Any, Dict, List, Optional

from app.models.document import Document
from app.models.document_analysis import DocumentAnalysis
from app.services.feature_engineering.exceptions import (
    InvalidFeatureVectorError,
    PreprocessingIncompleteError,
)
from app.services.feature_engineering.feature_registry import feature_registry
from app.services.feature_engineering.feature_schema import FeatureVector
from app.services.feature_engineering.file_features import extract_file_features
from app.services.feature_engineering.integrity_features import (
    extract_integrity_and_cross_source_features,
)
from app.services.feature_engineering.metadata_features import extract_metadata_features
from app.services.feature_engineering.normalization import BaseFeatureScaler
from app.services.feature_engineering.structural_features import (
    extract_structural_features,
)
from app.services.feature_engineering.text_features import extract_text_features

logger = logging.getLogger("app.services.feature_engineering.pipeline")

FEATURE_VERSION = "1.0"
PIPELINE_VERSION = "1.0.0"


class FeatureEngineeringPipeline:
    """
    Central pipeline converting Phase 2 DocumentAnalysis into an ML-ready FeatureVector.
    """

    def __init__(self, scaler: Optional[BaseFeatureScaler] = None):
        self.scaler = scaler
        self.registry = feature_registry

    def extract_features(
        self,
        document: Document,
        analysis: Optional[DocumentAnalysis],
    ) -> FeatureVector:
        """
        Execute feature extraction across all submodules.
        Validates completeness, types, and mathematical validity.
        """
        logger.info(f"Extracting ML features for document {document.document_id}")

        # 1. Validation of Preprocessing State
        if not analysis or document.processing_status != "completed":
            raise PreprocessingIncompleteError(
                f"Document '{document.document_id}' has processing_status='{document.processing_status}'. "
                "Feature engineering requires preprocessing to be completed."
            )

        merged_features: Dict[str, Any] = {}

        # 2. Extract File Features (Section 4)
        file_feats = extract_file_features(
            original_filename=document.original_filename,
            file_type=document.file_type,
            file_size=document.file_size,
            file_hash=document.file_hash,
            hash_algorithm=document.hash_algorithm,
        )
        merged_features.update(file_feats)

        # 3. Extract Text & Lexical Features (Sections 5, 6, 7)
        text_feats = extract_text_features(analysis.cleaned_text)
        merged_features.update(text_feats)

        # 4. Extract Metadata Features (Sections 8, 9)
        meta_feats = extract_metadata_features(analysis.metadata_json)
        merged_features.update(meta_feats)

        # 5. Extract Structural Features (Sections 10, 11, 12)
        struct_feats = extract_structural_features(
            structure=analysis.structural_data_json,
            raw_text=analysis.raw_text,
        )
        merged_features.update(struct_feats)

        # 6. Extract Integrity & Missingness Features (Sections 13, 14, 15)
        ocr_info = {
            "used": analysis.ocr_used,
            "status": analysis.ocr_status,
            "error_message": analysis.processing_error,
        }
        text_info = {
            "raw_text": analysis.raw_text,
            "word_count": analysis.word_count,
            "paragraph_count": analysis.paragraph_count,
        }
        integ_feats = extract_integrity_and_cross_source_features(
            file_hash=document.file_hash,
            hash_algorithm=document.hash_algorithm,
            text_data=text_info,
            metadata=analysis.metadata_json,
            structure=analysis.structural_data_json,
            ocr_info=ocr_info,
        )
        merged_features.update(integ_feats)

        # 7. Quality Validation & Schema Enforcement (Section 24)
        validated_features = self._validate_and_sanitize(merged_features)

        # 8. Deterministic Ordering (Section 18)
        ordered_names = self.registry.get_feature_names()
        ordered_values: List[Any] = []
        for name in ordered_names:
            ordered_values.append(validated_features[name])

        # 9. Optional Normalization (Section 17)
        normalized_features: Optional[Dict[str, float]] = None
        if self.scaler:
            normalized_features = self.scaler.transform(validated_features)

        vector = FeatureVector(
            document_id=document.document_id,
            feature_version=FEATURE_VERSION,
            pipeline_version=PIPELINE_VERSION,
            features=validated_features,
            feature_names=ordered_names,
            feature_values=ordered_values,
            normalized_features=normalized_features,
            extraction_timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            f"Successfully generated {len(ordered_names)} features for document {document.document_id}"
        )
        return vector

    def _validate_and_sanitize(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates feature count, data types, and checks for NaN/Infinity.
        Ensures negative values are prevented for counts and dimensions.
        """
        registered_names = self.registry.get_feature_names()
        sanitized: Dict[str, Any] = {}

        for name in registered_names:
            defn = self.registry.get(name)
            val = features.get(name)

            if val is None:
                val = defn.default_value

            # Check numeric validity (NaN, Inf)
            if isinstance(val, float):
                if math.isnan(val) or math.isinf(val):
                    raise InvalidFeatureVectorError(
                        f"Invalid numeric value '{val}' detected for feature '{name}'."
                    )
            elif isinstance(val, int):
                # Ensure count features cannot be negative
                if ("count" in name or "length" in name or "size" in name) and val < 0:
                    val = 0

            # Coerce types matching definition
            if defn.datatype == "integer":
                val = int(val)
            elif defn.datatype == "float":
                val = round(float(val), 6)
            elif defn.datatype == "boolean":
                val = bool(val)

            sanitized[name] = val

        return sanitized


# Global default pipeline instance
default_pipeline = FeatureEngineeringPipeline()
