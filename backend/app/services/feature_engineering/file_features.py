"""
File-level feature extractor.
Extracts metrics on file size, extension, MIME type, and safe filename characteristics
without exposing filesystem paths.
"""
from pathlib import Path
import re
from typing import Any, Dict


EXTENSION_ENCODING: Dict[str, int] = {
    "pdf": 1,
    "docx": 2,
    "doc": 3,
    "jpg": 4,
    "jpeg": 4,
    "png": 5,
    "tiff": 6,
    "tif": 6,
    "bmp": 7,
}

MIME_ENCODING: Dict[str, int] = {
    "application/pdf": 1,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 2,
    "application/msword": 3,
    "image/jpeg": 4,
    "image/jpg": 4,
    "image/png": 5,
    "image/tiff": 6,
    "image/bmp": 7,
}


def extract_file_features(
    original_filename: str,
    file_type: str,
    file_size: int,
    file_hash: str | None,
    hash_algorithm: str | None,
) -> Dict[str, Any]:
    """
    Extract file-level numerical and categorical features.
    Guarantees no server paths are leaked.
    """
    safe_filename = Path(original_filename).name
    ext = safe_filename.split(".")[-1].lower() if "." in safe_filename else ""

    file_size_bytes = int(max(0, file_size))
    file_size_kb = round(file_size_bytes / 1024.0, 3)
    file_size_mb = round(file_size_bytes / (1024.0 * 1024.0), 4)

    ext_code = EXTENSION_ENCODING.get(ext, 0)
    mime_code = MIME_ENCODING.get(file_type.lower() if file_type else "", 0)

    # Filename characteristics
    filename_len = len(safe_filename)
    digit_count = sum(1 for c in safe_filename if c.isdigit())
    special_char_count = sum(
        1 for c in safe_filename if not c.isalnum() and c not in (".", "_", "-")
    )
    # Check for 32/36-char hex UUID pattern
    has_uuid = bool(
        re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", safe_filename)
        or re.search(r"^[0-9a-fA-F]{32}", safe_filename)
    )

    has_hash = bool(file_hash and len(file_hash.strip()) > 0)

    return {
        "file_size_bytes": file_size_bytes,
        "file_size_kb": file_size_kb,
        "file_size_mb": file_size_mb,
        "file_extension_code": ext_code,
        "mime_type_code": mime_code,
        "has_hash": has_hash,
        "filename_length": filename_len,
        "filename_digit_count": digit_count,
        "filename_special_character_count": special_char_count,
        "filename_has_uuid_pattern": has_uuid,
    }
