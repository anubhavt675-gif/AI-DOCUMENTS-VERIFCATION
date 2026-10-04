"""
Feature service layer.
Coordinates feature generation, database persistence for DocumentFeatures records,
and dataset exports (CSV / JSON).
"""
import csv
from datetime import datetime, timezone
import io
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_analysis import DocumentAnalysis
from app.models.document_features import DocumentFeatures
from app.schemas.features import (
    DatasetExportResponse,
    FeatureGenerationResponse,
    FeatureVectorResponse,
)
from app.services.feature_engineering import (
    FEATURE_VERSION,
    PIPELINE_VERSION,
    PreprocessingIncompleteError,
    default_pipeline,
    feature_registry,
)

logger = logging.getLogger("app.services.feature_service")


def generate_document_features(db: Session, document_id: str) -> DocumentFeatures:
    """
    Executes the Feature Engineering Pipeline for a preprocessed document.
    Validates preprocessing completion, extracts and validates features,
    and persists the record in the database.
    """
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise ValueError(f"Document '{document_id}' not found.")

    analysis = (
        db.query(DocumentAnalysis)
        .filter(DocumentAnalysis.document_id == document_id)
        .first()
    )

    if doc.processing_status != "completed" or not analysis:
        status_msg = doc.processing_status or "pending"
        raise PreprocessingIncompleteError(
            f"Cannot engineer features for document '{document_id}'. "
            f"Preprocessing status is '{status_msg}'. Document preprocessing must be completed first."
        )

    # Execute pipeline
    vector = default_pipeline.extract_features(document=doc, analysis=analysis)

    # Upsert DocumentFeatures record
    df_record = (
        db.query(DocumentFeatures)
        .filter(DocumentFeatures.document_id == document_id)
        .first()
    )

    now = datetime.now(timezone.utc)
    if not df_record:
        df_record = DocumentFeatures(
            document_id=document_id,
            feature_version=vector.feature_version,
            pipeline_version=vector.pipeline_version,
            features_json=vector.features,
            feature_names_json=vector.feature_names,
            normalized_features_json=vector.normalized_features,
            extraction_timestamp=now,
            created_at=now,
        )
        db.add(df_record)
    else:
        df_record.feature_version = vector.feature_version
        df_record.pipeline_version = vector.pipeline_version
        df_record.features_json = vector.features
        df_record.feature_names_json = vector.feature_names
        df_record.normalized_features_json = vector.normalized_features
        df_record.extraction_timestamp = now

    db.commit()
    db.refresh(df_record)
    logger.info(f"Persisted {len(vector.feature_names)} features for document {document_id}")
    return df_record


def get_features_by_document_id(
    db: Session, document_id: str
) -> Optional[FeatureVectorResponse]:
    """
    Retrieve stored feature vector for a document.
    """
    df = (
        db.query(DocumentFeatures)
        .filter(DocumentFeatures.document_id == document_id)
        .first()
    )
    if not df:
        return None

    names = df.feature_names_json or feature_registry.get_feature_names()
    values = [df.features_json.get(name) for name in names]

    ts = df.extraction_timestamp
    ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)

    return FeatureVectorResponse(
        document_id=df.document_id,
        feature_version=df.feature_version,
        pipeline_version=df.pipeline_version,
        feature_count=len(names),
        feature_names=names,
        feature_values=values,
        features=df.features_json,
        normalized_features=df.normalized_features_json,
        extraction_timestamp=ts_str,
    )


def export_dataset_csv(db: Session) -> str:
    """
    Export all generated document feature records into a standardized ML-ready CSV.
    One row per document, one feature per column.
    """
    records = db.query(DocumentFeatures).all()
    feature_names = feature_registry.get_feature_names()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    header = ["document_id"] + feature_names
    writer.writerow(header)

    # Rows
    for rec in records:
        f_dict = rec.features_json or {}
        row = [rec.document_id] + [f_dict.get(name, "") for name in feature_names]
        writer.writerow(row)

    return output.getvalue()


def export_dataset_json(db: Session) -> DatasetExportResponse:
    """
    Export all generated document feature records into standardized JSON dataset.
    """
    records = db.query(DocumentFeatures).all()
    feature_names = feature_registry.get_feature_names()

    formatted_records: List[Dict[str, Any]] = []
    for rec in records:
        f_dict = rec.features_json or {}
        item = {"document_id": rec.document_id}
        for name in feature_names:
            item[name] = f_dict.get(name)
        formatted_records.append(item)

    return DatasetExportResponse(
        total_documents=len(formatted_records),
        feature_version=FEATURE_VERSION,
        feature_names=feature_names,
        records=formatted_records,
    )
