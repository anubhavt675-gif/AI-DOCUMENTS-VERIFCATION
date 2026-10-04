"""
Plain Text (.txt) Document Processor.
Extracts text content, computes basic structural metrics, and produces
standardized metadata for government text-format documents.
"""
import logging
from pathlib import Path
from typing import Any, Dict

from app.services.document_processing.base_processor import BaseDocumentProcessor
from app.services.document_processing.models import (
    DocumentFingerprint,
    OCRResult,
    ProcessingResult,
    StandardizedMetadata,
    TextExtractionResult,
)
from app.services.document_processing.text_cleaner import clean_text

logger = logging.getLogger(__name__)


class TextProcessor(BaseDocumentProcessor):
    """
    Processor for plain-text government documents (.txt).
    Performs text normalization, structure analysis, and basic metadata inference.
    """

    def process(
        self,
        file_path: Path,
        original_filename: str,
        document_id: str,
        fingerprint: DocumentFingerprint,
    ) -> ProcessingResult:
        logger.info(f"Processing plain-text document: {original_filename}")

        try:
            raw_text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return ProcessingResult(
                document_id=document_id,
                file_type="text/plain",
                fingerprint=fingerprint,
                text=TextExtractionResult(),
                metadata=StandardizedMetadata(),
                processing_error=f"Failed to read text file: {exc}",
            )

        # --- Text analysis ---
        cleaned = clean_text(raw_text) if raw_text.strip() else ""
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
        lines = [ln for ln in raw_text.splitlines() if ln.strip()]
        words = cleaned.split() if cleaned else []

        text_result = TextExtractionResult(
            raw_text=raw_text,
            cleaned_text=cleaned,
            word_count=len(words),
            character_count=len(raw_text),
            paragraph_count=len(paragraphs),
        )

        # --- Structure analysis ---
        heading_lines = [
            ln for ln in lines
            if len(ln) < 120 and (ln.isupper() or ln.startswith("##") or ln.endswith(":"))
        ]
        structure: Dict[str, Any] = {
            "format": "plain_text",
            "page_count": 1,
            "line_count": len(lines),
            "paragraph_count": len(paragraphs),
            "heading_count": len(heading_lines),
            "headings": heading_lines[:10],
            "character_count": len(raw_text),
            "estimated_word_count": len(words),
            "has_encoding_issues": "\ufffd" in raw_text,
        }

        # --- Metadata inference (no EXIF/PDF standard metadata for .txt) ---
        metadata = StandardizedMetadata(
            title=heading_lines[0][:200] if heading_lines else Path(original_filename).stem,
        )

        return ProcessingResult(
            document_id=document_id,
            file_type="text/plain",
            fingerprint=fingerprint,
            text=text_result,
            metadata=metadata,
            structure=structure,
            ocr=OCRResult(used=False, status="not_required"),
            page_count=1,
            paragraph_count=len(paragraphs),
        )
