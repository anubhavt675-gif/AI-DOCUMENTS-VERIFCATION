"""
Metadata standardization across PDF, DOCX, and Image formats.
"""
from datetime import datetime, timezone
import re
from typing import Any, Dict, Optional

from app.services.document_processing.models import StandardizedMetadata


def parse_date_to_iso(value: Any) -> Optional[str]:
    """
    Safely parse various date formats into an ISO 8601 string.
    Supports:
    - datetime objects
    - PDF date strings: D:YYYYMMDDHHmmSS[+|-]HH'mm' or D:YYYYMMDDHHmmSSZ
    - EXIF date strings: YYYY:MM:DD HH:MM:SS
    - Standard ISO 8601 strings
    """
    if not value:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

    val_str = str(value).strip()
    if not val_str:
        return None

    # Handle PDF format: D:20240315123000Z or D:20240315123000+05'30'
    if val_str.startswith("D:"):
        clean_pdf_date = val_str[2:]
        # Extract YYYYMMDDHHMMSS
        match = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?", clean_pdf_date)
        if match:
            year, month, day = match.group(1), match.group(2), match.group(3)
            hour = match.group(4) or "00"
            minute = match.group(5) or "00"
            second = match.group(6) or "00"
            try:
                dt = datetime(
                    int(year), int(month), int(day),
                    int(hour), int(minute), int(second),
                    tzinfo=timezone.utc
                )
                return dt.isoformat()
            except ValueError:
                pass

    # Handle EXIF format: 2024:03:15 12:30:00
    if re.match(r"^\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}", val_str):
        try:
            parts = val_str.split(" ")
            date_part = parts[0].replace(":", "-")
            iso_candidate = f"{date_part}T{parts[1]}+00:00"
            dt = datetime.fromisoformat(iso_candidate)
            return dt.isoformat()
        except Exception:
            pass

    # Try standard ISO format parse
    try:
        dt = datetime.fromisoformat(val_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        pass

    return None


def clean_string_field(value: Any) -> Optional[str]:
    """Return non-empty trimmed string or None."""
    if value is None:
        return None
    val_str = str(value).strip()
    return val_str if val_str else None


def standardize_metadata(raw_dict: Dict[str, Any]) -> StandardizedMetadata:
    """
    Map format-specific metadata dictionary into standardized schema.
    Missing fields become None. Never invents data.
    """
    title = clean_string_field(raw_dict.get("title"))
    author = clean_string_field(raw_dict.get("author") or raw_dict.get("creator_name"))
    subject = clean_string_field(raw_dict.get("subject") or raw_dict.get("description"))
    creator = clean_string_field(raw_dict.get("creator") or raw_dict.get("software"))
    producer = clean_string_field(raw_dict.get("producer"))
    keywords = clean_string_field(raw_dict.get("keywords") or raw_dict.get("tags"))
    last_modified_by = clean_string_field(raw_dict.get("last_modified_by"))

    created_at = parse_date_to_iso(
        raw_dict.get("created_at")
        or raw_dict.get("created")
        or raw_dict.get("creationDate")
        or raw_dict.get("DateTimeOriginal")
    )
    modified_at = parse_date_to_iso(
        raw_dict.get("modified_at")
        or raw_dict.get("modified")
        or raw_dict.get("modDate")
        or raw_dict.get("DateTime")
    )

    return StandardizedMetadata(
        title=title,
        author=author,
        subject=subject,
        creator=creator,
        producer=producer,
        keywords=keywords,
        created_at=created_at,
        modified_at=modified_at,
        last_modified_by=last_modified_by,
    )
