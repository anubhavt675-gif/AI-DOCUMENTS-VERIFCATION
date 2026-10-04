"""
DOCX processor using python-docx.
Extracts paragraphs, headings, tables, embedded images, core properties, and structural metrics.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List
import zipfile

import docx
from docx.opc.exceptions import PackageNotFoundError

from app.services.document_processing.base_processor import BaseDocumentProcessor
from app.services.document_processing.exceptions import (
    CorruptedDocumentError,
    EmptyDocumentError,
    ExtractionError,
)
from app.services.document_processing.metadata_extractor import standardize_metadata
from app.services.document_processing.models import (
    DocumentFingerprint,
    OCRResult,
    ProcessingResult,
)
from app.services.document_processing.structural_analyzer import analyze_docx_structure
from app.services.document_processing.text_cleaner import process_text_extraction

logger = logging.getLogger("app.services.document_processing.docx")


class DOCXProcessor(BaseDocumentProcessor):
    """
    Extracts text, tables, core properties, and structural layout from DOCX files.
    """

    def process(
        self,
        file_path: Path,
        original_filename: str,
        document_id: str,
        fingerprint: DocumentFingerprint,
    ) -> ProcessingResult:
        logger.info(f"Starting DOCX extraction for document {document_id} ({original_filename})")

        if not file_path.exists() or file_path.stat().st_size == 0:
            raise EmptyDocumentError(f"DOCX document '{original_filename}' is empty or does not exist.")

        try:
            doc = docx.Document(file_path)
        except (PackageNotFoundError, zipfile.BadZipFile, Exception) as exc:
            logger.error(f"Failed to open DOCX {original_filename}: {exc}")
            raise CorruptedDocumentError(f"Corrupted or invalid DOCX document: {exc}") from exc

        try:
            # 1. Core properties (metadata)
            raw_meta: Dict[str, Any] = {}
            try:
                cp = doc.core_properties
                raw_meta = {
                    "title": cp.title,
                    "author": cp.author,
                    "subject": cp.subject,
                    "keywords": cp.keywords,
                    "created": cp.created,
                    "modified": cp.modified,
                    "last_modified_by": cp.last_modified_by,
                }
            except Exception as meta_exc:
                logger.warning(f"Could not read DOCX core properties for {document_id}: {meta_exc}")

            standardized_meta = standardize_metadata(raw_meta)

            # 2. Paragraphs & Headings
            paragraph_texts: List[str] = []
            heading_texts: List[str] = []
            for p in doc.paragraphs:
                p_text = p.text.strip()
                if p_text:
                    paragraph_texts.append(p_text)
                    style_name = getattr(p.style, "name", "") or ""
                    if "heading" in style_name.lower():
                        heading_texts.append(p_text)

            # 3. Tables
            table_texts: List[str] = []
            tables_info: List[Dict[str, int]] = []
            for t_idx, table in enumerate(doc.tables):
                row_count = len(table.rows)
                col_count = len(table.columns) if row_count > 0 else 0
                tables_info.append({"table_index": t_idx + 1, "rows": row_count, "columns": col_count})

                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        # Deduplicate adjacent cells if merged
                        clean_row = []
                        prev = None
                        for c in row_cells:
                            if c != prev:
                                clean_row.append(c)
                                prev = c
                        if clean_row:
                            table_texts.append(" | ".join(clean_row))

            # 4. Embedded Images
            image_count = len(doc.inline_shapes)
            try:
                for rel in doc.part.rels.values():
                    if "image" in rel.target_ref.lower():
                        image_count = max(image_count, len([r for r in doc.part.rels.values() if "image" in r.target_ref.lower()]))
            except Exception:
                pass

            # 5. Hyperlinks
            hyperlink_count = 0
            try:
                for rel in doc.part.rels.values():
                    if "hyperlink" in rel.reltype.lower():
                        hyperlink_count += 1
            except Exception:
                pass

            # Section / Page info estimate
            section_count = len(doc.sections)

            # Combine all text
            all_text_blocks = paragraph_texts + table_texts
            raw_full_text = "\n\n".join(all_text_blocks)
            text_result = process_text_extraction(raw_full_text)

            structure = analyze_docx_structure(
                paragraph_count=len(doc.paragraphs),
                heading_count=len(heading_texts),
                headings=heading_texts,
                table_count=len(doc.tables),
                tables_info=tables_info,
                image_count=image_count,
                hyperlink_count=hyperlink_count,
            )
            structure["section_count"] = section_count

            ocr_result = OCRResult(
                used=False,
                status="not_required",
                extracted_text="",
            )

            logger.info(
                f"DOCX extraction completed for {document_id}: "
                f"{len(doc.paragraphs)} paragraphs, {len(doc.tables)} tables, "
                f"{text_result.word_count} words."
            )

            return ProcessingResult(
                document_id=document_id,
                file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                fingerprint=fingerprint,
                text=text_result,
                metadata=standardized_meta,
                structure=structure,
                ocr=ocr_result,
                page_count=max(1, section_count),
                image_count=image_count,
                table_count=len(doc.tables),
                paragraph_count=len(doc.paragraphs),
            )

        except (EmptyDocumentError, CorruptedDocumentError):
            raise
        except Exception as exc:
            logger.error(f"Unexpected error extracting DOCX {document_id}: {exc}")
            raise ExtractionError(f"Failed to extract DOCX data: {exc}") from exc
