"""
File security utilities: validation, sanitization, path-traversal prevention.
"""
import mimetypes
import os
import re
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException, status

from app.config import get_settings

settings = get_settings()


def sanitize_filename(filename: str) -> str:
    """
    Strip directory components and replace any character that is not
    alphanumeric, a dot, hyphen, or underscore.
    """
    # Remove any path components supplied by the client
    filename = Path(filename).name
    # Replace dangerous characters
    filename = re.sub(r"[^\w.\-]", "_", filename)
    # Prevent filenames that start with a dot (hidden files on Unix)
    filename = filename.lstrip(".")
    return filename or "file"


def get_safe_extension(filename: str) -> str:
    """Return lowercased extension including the leading dot, e.g. '.pdf'."""
    return Path(filename).suffix.lower()


def generate_stored_filename(original_filename: str) -> str:
    """
    Build a stored filename that is unique and carries no user-supplied path info.
    Format: <uuid4>_<sanitized-original>
    """
    safe_name = sanitize_filename(original_filename)
    unique_id = uuid.uuid4().hex
    return f"{unique_id}_{safe_name}"


def validate_extension(filename: str) -> None:
    ext = get_safe_extension(filename)
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not allowed. "
                   f"Accepted: {', '.join(sorted(settings.allowed_extensions))}",
        )


def validate_mime_type(content_type: str) -> None:
    if content_type not in settings.allowed_file_types_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type '{content_type}' is not accepted.",
        )


def validate_file_size(size: int) -> None:
    if size > settings.max_file_size:
        max_mb = settings.max_file_size / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the maximum allowed size of {max_mb:.0f} MB.",
        )


def get_upload_path(stored_filename: str) -> Path:
    """
    Return an absolute, canonical path inside the uploads directory.
    Raises if the resolved path escapes the upload root (path-traversal guard).
    """
    upload_root = Path(settings.upload_dir).resolve()
    target = (upload_root / stored_filename).resolve()

    if not str(target).startswith(str(upload_root)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path.",
        )
    return target


async def save_upload_file(upload_file: UploadFile, stored_filename: str) -> int:
    """
    Stream the upload to disk.  Returns the actual number of bytes written.
    Never executes the file.
    """
    upload_root = Path(settings.upload_dir).resolve()
    upload_root.mkdir(parents=True, exist_ok=True)

    target_path = get_upload_path(stored_filename)
    total_bytes = 0

    with open(target_path, "wb") as out:
        while chunk := await upload_file.read(1024 * 64):  # 64 KB chunks
            total_bytes += len(chunk)
            if total_bytes > settings.max_file_size:
                out.close()
                os.remove(target_path)
                raise HTTPException(
                    status_code=413,
                    detail="File exceeds the maximum allowed size.",
                )
            out.write(chunk)

    return total_bytes
