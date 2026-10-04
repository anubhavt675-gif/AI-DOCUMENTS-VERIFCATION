"""
Image processor using Pillow (PIL) and optional Tesseract OCR.
Extracts dimensions, color mode, format, EXIF tags, and optional OCR text.
Degrades gracefully if OCR engine is unavailable or encounters errors.
"""
import logging
from pathlib import Path
from typing import Any, Dict

from PIL import ExifTags, Image, UnidentifiedImageError

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
from app.services.document_processing.structural_analyzer import analyze_image_structure
from app.services.document_processing.text_cleaner import process_text_extraction

logger = logging.getLogger("app.services.document_processing.image")


class ImageProcessor(BaseDocumentProcessor):
    """
    Extracts image metadata, EXIF, and runs OCR if engine is locally installed.
    """

    def process(
        self,
        file_path: Path,
        original_filename: str,
        document_id: str,
        fingerprint: DocumentFingerprint,
    ) -> ProcessingResult:
        logger.info(f"Starting Image extraction for document {document_id} ({original_filename})")

        if not file_path.exists() or file_path.stat().st_size == 0:
            raise EmptyDocumentError(f"Image document '{original_filename}' is empty or does not exist.")

        file_size = file_path.stat().st_size

        try:
            with Image.open(file_path) as img:
                img_format = (img.format or "").upper()
                width, height = img.size
                color_mode = img.mode

                if width <= 0 or height <= 0:
                    raise EmptyDocumentError(f"Image '{original_filename}' has invalid dimensions: {width}x{height}")

                # 1. EXIF extraction
                raw_meta: Dict[str, Any] = {}
                has_exif = False
                try:
                    exif_data = img.getexif()
                    if exif_data:
                        has_exif = True
                        for tag_id, value in exif_data.items():
                            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                            raw_meta[tag_name] = value

                        # Map EXIF fields
                        if "Artist" in raw_meta and not raw_meta.get("author"):
                            raw_meta["author"] = raw_meta["Artist"]
                        if "ImageDescription" in raw_meta and not raw_meta.get("title"):
                            raw_meta["title"] = raw_meta["ImageDescription"]
                        if "Software" in raw_meta and not raw_meta.get("creator"):
                            raw_meta["creator"] = raw_meta["Software"]
                except Exception as exif_err:
                    logger.warning(f"Could not read EXIF data for {document_id}: {exif_err}")

                standardized_meta = standardize_metadata(raw_meta)

                # 2. Structural Analysis
                structure = analyze_image_structure(
                    width=width,
                    height=height,
                    color_mode=color_mode,
                    image_format=img_format or "IMAGE",
                    has_exif=has_exif,
                    file_size=file_size,
                )

                # 3. Modular OCR Extraction
                ocr_result = self._perform_ocr(img, document_id)

                # 4. Text Processing
                raw_text = ocr_result.extracted_text if ocr_result.used else ""
                text_result = process_text_extraction(raw_text)

                logger.info(
                    f"Image extraction completed for {document_id}: "
                    f"{width}x{height} {img_format}, OCR status={ocr_result.status}, "
                    f"words extracted={text_result.word_count}"
                )

                mime_type = f"image/{img_format.lower()}" if img_format else "image/jpeg"

                return ProcessingResult(
                    document_id=document_id,
                    file_type=mime_type,
                    fingerprint=fingerprint,
                    text=text_result,
                    metadata=standardized_meta,
                    structure=structure,
                    ocr=ocr_result,
                    page_count=1,
                    image_count=1,
                    table_count=0,
                    paragraph_count=text_result.paragraph_count,
                )

        except (EmptyDocumentError, CorruptedDocumentError):
            raise
        except UnidentifiedImageError as uie:
            logger.error(f"Pillow cannot identify image {original_filename}: {uie}")
            raise CorruptedDocumentError(f"Corrupted or invalid image file: {uie}") from uie
        except Exception as exc:
            logger.error(f"Unexpected error processing image {document_id}: {exc}")
            raise ExtractionError(f"Failed to process image file: {exc}") from exc

    def _perform_ocr(self, img: Image.Image, document_id: str) -> OCRResult:
        """
        Safely attempts OCR extraction using pytesseract.
        Degrades gracefully without raising exceptions if tesseract is missing or fails.
        """
        logger.info(f"Checking OCR capability for {document_id}")
        try:
            import pytesseract
            # Run image_to_string
            ocr_text = pytesseract.image_to_string(img)
            clean_ocr = (ocr_text or "").strip()
            logger.info(f"OCR successfully completed for {document_id} ({len(clean_ocr)} characters)")
            return OCRResult(
                used=True,
                status="completed",
                extracted_text=clean_ocr,
                error_message=None,
            )
        except (pytesseract.TesseractNotFoundError, FileNotFoundError) as nf_err:
            logger.info(f"OCR engine not available for {document_id}: {nf_err}")
            return OCRResult(
                used=False,
                status="unavailable",
                extracted_text="",
                error_message="Tesseract OCR engine is not installed or not configured in system PATH.",
            )
        except Exception as ocr_err:
            logger.warning(f"OCR processing failed for {document_id}: {ocr_err}")
            return OCRResult(
                used=False,
                status="failed",
                extracted_text="",
                error_message=f"OCR execution failed: {str(ocr_err)}",
            )
