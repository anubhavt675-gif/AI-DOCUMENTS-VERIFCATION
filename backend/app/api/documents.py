"""
Document API router — upload, list, retrieve.
"""
import uuid
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db, _get_session_local
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    ErrorResponse,
    UploadResponse,
)
from app.schemas.features import (
    DatasetExportResponse,
    FeatureGenerationResponse,
    FeatureRegistryItem,
    FeatureRegistryResponse,
    FeatureVectorResponse,
)
from app.schemas.processing import DocumentAnalysisResponse, ProcessResponse
from app.services.document_service import (
    create_document,
    get_document_by_document_id,
    list_documents,
)
from app.services.feature_engineering import (
    FEATURE_VERSION,
    PIPELINE_VERSION,
    PreprocessingIncompleteError,
    feature_registry,
)
from app.services.feature_service import (
    export_dataset_csv,
    export_dataset_json,
    generate_document_features,
    get_features_by_document_id,
)
from app.services.processing_service import (
    get_analysis_by_document_id,
    run_document_preprocessing,
)
from app.ml.inference.predictor import AnomalyPredictor
from app.ml.schemas import PredictionResultSchema
from app.utils.file_utils import (
    generate_stored_filename,
    save_upload_file,
    validate_extension,
    validate_file_size,
    validate_mime_type,
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


def _run_preprocessing_background(document_id: str) -> None:
    """Helper executed by FastAPI BackgroundTasks to process document asynchronously."""
    session_factory = _get_session_local()
    db = session_factory()
    try:
        run_document_preprocessing(db, document_id)
    finally:
        db.close()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document for integrity verification",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Accept PDF / DOCX / image files, validate them, save securely,
    create database records, and kick off automatic document preprocessing.
    """
    # 1. Validate content type header (first defence)
    content_type = file.content_type or ""
    validate_mime_type(content_type)

    # 2. Validate file extension
    validate_extension(file.filename or "")

    # 3. Build secure stored filename
    stored_filename = generate_stored_filename(file.filename or "upload")
    new_document_id = str(uuid.uuid4())

    # 4. Stream to disk while checking size
    actual_size = await save_upload_file(file, stored_filename)

    # 5. Also validate declared / actual size
    validate_file_size(actual_size)

    # 6. Persist record
    data = DocumentCreate(
        document_id=new_document_id,
        original_filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        file_type=content_type,
        file_size=actual_size,
    )
    doc = create_document(db, data)

    # 7. Queue automatic background preprocessing pipeline (Phase 2)
    background_tasks.add_task(_run_preprocessing_background, doc.document_id)

    return UploadResponse(
        success=True,
        document_id=doc.document_id,
        filename=doc.original_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all uploaded documents",
)
def list_all_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    docs, total = list_documents(db, skip=skip, limit=limit)
    return DocumentListResponse(
        success=True,
        total=total,
        documents=[DocumentResponse.model_validate(d) for d in docs],
    )


@router.get(
    "/features/registry",
    response_model=FeatureRegistryResponse,
    summary="Inspect the feature registry definitions (Phase 3)",
)
def get_feature_registry():
    """Returns all engineered feature specifications from the centralized registry."""
    features = [
        FeatureRegistryItem(
            name=f.name,
            category=f.category,
            datatype=f.datatype,
            description=f.description,
            source=f.source,
            nullable=f.nullable,
            default_value=f.default_value,
            normalization=f.normalization,
        )
        for f in feature_registry.list_features()
    ]
    return FeatureRegistryResponse(
        total_features=len(features),
        features=features,
    )


@router.get(
    "/features/dataset",
    summary="Export ML-ready dataset in CSV or JSON format (Phase 3)",
)
def export_features_dataset(
    format: str = Query("json", enum=["csv", "json"], description="Export format: 'csv' or 'json'"),
    db: Session = Depends(get_db),
):
    """
    Exports all extracted features for all documents into a standardized dataset.
    One row per document, one feature per column.
    """
    if format.lower() == "csv":
        csv_data = export_dataset_csv(db)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="document_ml_dataset.csv"'},
        )
    return export_dataset_json(db)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Retrieve a single document by its UUID",
    responses={404: {"model": ErrorResponse}},
)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = get_document_by_document_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return DocumentResponse.model_validate(doc)


@router.post(
    "/{document_id}/process",
    response_model=ProcessResponse,
    summary="Start document preprocessing",
    responses={404: {"model": ErrorResponse}},
)
def process_document_endpoint(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Trigger or re-trigger document preprocessing for a specific document.
    """
    doc = get_document_by_document_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    updated_doc = run_document_preprocessing(db, document_id)
    return ProcessResponse(
        success=updated_doc.processing_status == "completed",
        document_id=updated_doc.document_id,
        processing_status=updated_doc.processing_status or "completed",
        message="Preprocessing executed successfully." if updated_doc.processing_status == "completed" else "Preprocessing encountered an issue.",
    )


@router.get(
    "/{document_id}/analysis",
    response_model=DocumentAnalysisResponse,
    summary="Retrieve standardized document preprocessing analysis result",
    responses={404: {"model": ErrorResponse}},
)
def get_analysis_endpoint(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns standardized text extraction, metadata, structural analysis,
    and OCR status without exposing sensitive filesystem paths.
    """
    analysis_data = get_analysis_by_document_id(db, document_id)
    if not analysis_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return analysis_data


@router.post(
    "/{document_id}/features",
    response_model=FeatureGenerationResponse,
    summary="Generate ML-ready feature vector for a preprocessed document (Phase 3)",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def generate_features_endpoint(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Runs the Feature Engineering Pipeline.
    Verifies preprocessing has completed before generating features.
    """
    doc = get_document_by_document_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    try:
        df_record = generate_document_features(db, document_id)
        count = len(df_record.feature_names_json or [])
        return FeatureGenerationResponse(
            success=True,
            document_id=document_id,
            feature_version=df_record.feature_version,
            feature_count=count,
            status="completed",
            message=f"Successfully extracted {count} standardized ML features.",
        )
    except PreprocessingIncompleteError as pie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(pie),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature extraction failed: {str(exc)}",
        )


@router.get(
    "/{document_id}/features",
    response_model=FeatureVectorResponse,
    summary="Retrieve engineered ML feature vector for a document (Phase 3)",
    responses={404: {"model": ErrorResponse}},
)
def get_features_endpoint(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves the ordered, standardized feature vector for downstream ML models.
    """
    features_resp = get_features_by_document_id(db, document_id)
    if not features_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No engineered features found for document '{document_id}'. Please run feature extraction first.",
        )
    return features_resp


# ML singleton predictor
_predictor = AnomalyPredictor()


@router.post(
    "/{document_id}/predict",
    response_model=PredictionResultSchema,
    summary="Run Isolation Forest anomaly detection inference on document (Phase 4)",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def predict_document_endpoint(
    document_id: str,
    threshold: Optional[float] = Query(default=None, description="Optional custom anomaly threshold override"),
    db: Session = Depends(get_db),
):
    """
    Consumes Phase 3 feature vectors, transforms with pre-fitted scaler,
    and runs active Isolation Forest model to compute raw score, normalized score,
    and explainability feature deviations.
    """
    try:
        return _predictor.predict_document(document_id, db, custom_threshold=threshold)
    except ValueError as ve:
        # Document not found or missing features
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        # Missing active model
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(re))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(exc)}",
        )


@router.get(
    "/{document_id}/predictions",
    response_model=List[PredictionResultSchema],
    summary="Retrieve prediction history for document (Phase 4)",
    responses={404: {"model": ErrorResponse}},
)
def get_document_predictions_endpoint(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns full history of anomaly detection predictions for the specified document,
    ordered with the latest prediction first.
    """
    doc = get_document_by_document_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return _predictor.get_document_predictions(document_id, db)

