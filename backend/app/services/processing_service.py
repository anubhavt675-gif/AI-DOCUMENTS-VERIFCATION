"""
Processing service layer.
Coordinates document preprocessing, database persistence for analysis records,
and status transitions (pending -> processing -> completed / failed).
"""
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.document import Document
from app.models.document_analysis import DocumentAnalysis
from app.schemas.processing import (
    DocumentAnalysisResponse,
    FileAnalysisSummary,
    OCRAnalysisSummary,
    TextAnalysisSummary,
)
from app.services.document_processing import (
    ProcessingError,
    calculate_sha256,
    process_document,
)

logger = logging.getLogger("app.services.processing_service")


def get_stored_file_path(stored_filename: str) -> Path:
    """Resolve stored filename to absolute path within upload directory."""
    settings = get_settings()
    return Path(settings.upload_dir) / stored_filename


def run_document_preprocessing(db: Session, document_id: str) -> Document:
    """
    Executes the preprocessing pipeline for a given document.
    Updates Document and DocumentAnalysis records in the database.
    Does not crash the application if an individual document fails.
    """
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise ValueError(f"Document '{document_id}' not found.")

    file_path = get_stored_file_path(doc.stored_filename)

    logger.info(f"Starting preprocessing for document_id={document_id}, file={doc.original_filename}")
    doc.processing_status = "processing"
    db.commit()
    db.refresh(doc)

    # Check or compute file hash
    try:
        if not doc.file_hash and file_path.exists():
            doc.file_hash = calculate_sha256(file_path)
            doc.hash_algorithm = "SHA-256"
            db.commit()
    except Exception as hash_err:
        logger.warning(f"Could not calculate initial hash for {document_id}: {hash_err}")

    # Fetch or create analysis record
    analysis = (
        db.query(DocumentAnalysis)
        .filter(DocumentAnalysis.document_id == document_id)
        .first()
    )
    if not analysis:
        analysis = DocumentAnalysis(document_id=document_id)
        db.add(analysis)

    try:
        if not file_path.exists():
            raise FileNotFoundError(f"Underlying file not found on disk: {doc.stored_filename}")

        result = process_document(
            file_path=file_path,
            original_filename=doc.original_filename,
            document_id=document_id,
            file_type=doc.file_type,
        )

        # Update Document record
        doc.file_hash = result.fingerprint.hash
        doc.hash_algorithm = result.fingerprint.algorithm
        doc.processing_status = "completed"

        # Update Analysis record
        analysis.raw_text = result.text.raw_text
        analysis.cleaned_text = result.text.cleaned_text
        analysis.word_count = result.text.word_count
        analysis.character_count = result.text.character_count
        analysis.page_count = result.page_count
        analysis.image_count = result.image_count
        analysis.table_count = result.table_count
        analysis.paragraph_count = result.paragraph_count
        analysis.metadata_json = result.metadata.to_dict()
        analysis.structural_data_json = result.structure
        analysis.ocr_used = result.ocr.used
        analysis.ocr_status = result.ocr.status
        analysis.processing_error = None

        db.commit()
        db.refresh(doc)
        db.refresh(analysis)
        logger.info(f"Preprocessing completed successfully for document_id={document_id}")
        return doc

    except Exception as exc:
        logger.error(f"Preprocessing failed for document_id={document_id}: {exc}", exc_info=True)
        doc.processing_status = "failed"
        analysis.processing_error = str(exc)
        if not analysis.ocr_status or analysis.ocr_status == "not_required":
            analysis.ocr_status = "failed"

        db.commit()
        db.refresh(doc)
        db.refresh(analysis)
        return doc


def get_analysis_by_document_id(
    db: Session, document_id: str
) -> Optional[DocumentAnalysisResponse]:
    """
    Retrieve standardized analysis results for an uploaded document.
    """
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        return None

    analysis = (
        db.query(DocumentAnalysis)
        .filter(DocumentAnalysis.document_id == document_id)
        .first()
    )

    file_summary = FileAnalysisSummary(
        filename=doc.original_filename,
        type=doc.file_type,
        size=doc.file_size,
        hash=doc.file_hash,
        hash_algorithm=doc.hash_algorithm or "SHA-256",
    )

    if analysis:
        text_summary = TextAnalysisSummary(
            raw_text=analysis.raw_text or "",
            cleaned_text=analysis.cleaned_text or "",
            word_count=analysis.word_count,
            character_count=analysis.character_count,
            paragraph_count=analysis.paragraph_count,
        )
        ocr_summary = OCRAnalysisSummary(
            used=analysis.ocr_used,
            status=analysis.ocr_status,
            error_message=analysis.processing_error if analysis.ocr_status == "failed" else None,
        )
        metadata_dict = analysis.metadata_json or {}
        structure_dict = analysis.structural_data_json or {}
        error_msg = analysis.processing_error
    else:
        text_summary = TextAnalysisSummary()
        ocr_summary = OCRAnalysisSummary(used=False, status="pending")
        metadata_dict = {}
        structure_dict = {}
        error_msg = None

    return DocumentAnalysisResponse(
        document_id=doc.document_id,
        file=file_summary,
        text=text_summary,
        metadata=metadata_dict,
        structure=structure_dict,
        ocr=ocr_summary,
        processing_status=doc.processing_status or "pending",
        processing_error=error_msg,
    )
