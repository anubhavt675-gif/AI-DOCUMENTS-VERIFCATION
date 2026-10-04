"""
PDF processor using PyMuPDF (fitz).
Extracts text, metadata, page dimensions, fonts, images, links, and layout structure.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Set

import fitz  # PyMuPDF

from app.services.document_processing.base_processor import BaseDocumentProcessor
from app.services.document_processing.exceptions import (
    CorruptedDocumentError,
    EmptyDocumentError,
    ExtractionError,
    PasswordProtectedError,
)
from app.services.document_processing.metadata_extractor import standardize_metadata
from app.services.document_processing.models import (
    DocumentFingerprint,
    OCRResult,
    ProcessingResult,
)
from app.services.document_processing.structural_analyzer import analyze_pdf_structure
from app.services.document_processing.text_cleaner import process_text_extraction

logger = logging.getLogger("app.services.document_processing.pdf")


class PDFProcessor(BaseDocumentProcessor):
    """
    Extracts text, structural metrics, and standardized metadata from PDF files.
    """

    def process(
        self,
        file_path: Path,
        original_filename: str,
        document_id: str,
        fingerprint: DocumentFingerprint,
    ) -> ProcessingResult:
        logger.info(f"Starting PDF extraction for document {document_id} ({original_filename})")

        if not file_path.exists() or file_path.stat().st_size == 0:
            raise EmptyDocumentError(f"PDF document '{original_filename}' is empty or does not exist.")

        doc = None
        try:
            doc = fitz.open(file_path)
        except Exception as exc:
            logger.error(f"Failed to open PDF {original_filename}: {exc}")
            raise CorruptedDocumentError(f"Corrupted or invalid PDF file: {exc}") from exc

        try:
            if doc.is_encrypted:
                logger.warning(f"PDF {original_filename} is encrypted / password protected.")
                raise PasswordProtectedError(f"PDF document '{original_filename}' is password protected.")

            page_count = doc.page_count
            if page_count == 0:
                raise EmptyDocumentError(f"PDF document '{original_filename}' contains 0 pages.")

            # Extract metadata
            raw_meta = doc.metadata or {}
            standardized_meta = standardize_metadata(raw_meta)

            pages_data: List[Dict[str, Any]] = []
            raw_text_parts: List[str] = []
            total_images = 0
            total_links = 0
            fonts_collected: Set[str] = set()
            font_sizes_collected: List[float] = []

            for page_index in range(page_count):
                page = doc.load_page(page_index)
                page_rect = page.rect
                page_text = page.get_text("text") or ""
                raw_text_parts.append(page_text)

                # Images on this page
                img_list = page.get_images(full=True)
                img_count = len(img_list)
                total_images += img_count

                # Links on this page
                links = page.get_links()
                total_links += len(links)

                # Blocks & font info safely extracted
                block_count = 0
                try:
                    text_dict = page.get_text("dict")
                    blocks = text_dict.get("blocks", [])
                    block_count = len(blocks)
                    for block in blocks:
                        if "lines" in block:
                            for line in block["lines"]:
                                for span in line.get("spans", []):
                                    font_name = span.get("font")
                                    if font_name:
                                        fonts_collected.add(font_name)
                                    font_size = span.get("size")
                                    if font_size and isinstance(font_size, (int, float)):
                                        font_sizes_collected.append(float(font_size))
                except Exception as font_exc:
                    logger.debug(f"Font extraction skipped on page {page_index + 1}: {font_exc}")

                pages_data.append({
                    "page_number": page_index + 1,
                    "width": page_rect.width,
                    "height": page_rect.height,
                    "text_length": len(page_text.strip()),
                    "image_count": img_count,
                    "block_count": block_count,
                })

            raw_full_text = "\n\n".join(raw_text_parts)
            text_result = process_text_extraction(raw_full_text)

            structure = analyze_pdf_structure(
                pages_data=pages_data,
                total_images=total_images,
                total_links=total_links,
                fonts_collected=fonts_collected,
                font_sizes_collected=font_sizes_collected,
            )

            ocr_result = OCRResult(
                used=False,
                status="not_required",
                extracted_text="",
            )

            logger.info(
                f"PDF extraction completed for {document_id}: "
                f"{page_count} pages, {text_result.word_count} words, {total_images} images."
            )

            return ProcessingResult(
                document_id=document_id,
                file_type="application/pdf",
                fingerprint=fingerprint,
                text=text_result,
                metadata=standardized_meta,
                structure=structure,
                ocr=ocr_result,
                page_count=page_count,
                image_count=total_images,
                table_count=0,  # PDFs do not reliably declare table structures without heuristic ML
                paragraph_count=text_result.paragraph_count,
            )

        except (EmptyDocumentError, PasswordProtectedError, CorruptedDocumentError):
            raise
        except Exception as exc:
            logger.error(f"Unexpected error extracting PDF {document_id}: {exc}")
            raise ExtractionError(f"Failed to extract PDF data: {exc}") from exc
        finally:
            if doc:
                try:
                    doc.close()
                except Exception:
                    pass
