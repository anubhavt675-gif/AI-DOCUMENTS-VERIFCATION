"""
Metadata and metadata consistency feature extractor.
Processes standardized metadata produced in Phase 2.
Produces numerical/boolean features and consistency ratios without making anomaly decisions.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional


EXPECTED_FIELDS = [
    "title",
    "author",
    "subject",
    "creator",
    "producer",
    "keywords",
    "created_at",
    "modified_at",
    "last_modified_by",
]


def parse_year_from_iso(iso_str: Optional[str]) -> int:
    """Extract 4-digit calendar year from ISO timestamp or return 0."""
    if not iso_str:
        return 0
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.year
    except Exception:
        return 0


def calculate_age_days(iso_str: Optional[str]) -> float:
    """Calculate days between creation date and current UTC time, or -1.0 if missing."""
    if not iso_str:
        return -1.0
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - dt
        return round(max(0.0, delta.total_seconds() / 86400.0), 2)
    except Exception:
        return -1.0


def extract_metadata_features(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract factual metadata availability, lengths, date relationships, and completeness ratios.
    """
    meta = metadata or {}

    title = meta.get("title")
    author = meta.get("author")
    subject = meta.get("subject")
    creator = meta.get("creator")
    producer = meta.get("producer")
    keywords = meta.get("keywords")
    created_at = meta.get("created_at")
    modified_at = meta.get("modified_at")
    last_modified_by = meta.get("last_modified_by")

    has_title = bool(title and str(title).strip())
    has_author = bool(author and str(author).strip())
    has_subject = bool(subject and str(subject).strip())
    has_creator = bool(creator and str(creator).strip())
    has_producer = bool(producer and str(producer).strip())
    has_keywords = bool(keywords and str(keywords).strip())
    has_creation_date = bool(created_at and str(created_at).strip())
    has_modification_date = bool(modified_at and str(modified_at).strip())
    has_last_modified_by = bool(last_modified_by and str(last_modified_by).strip())

    title_len = len(str(title).strip()) if has_title else 0
    author_len = len(str(author).strip()) if has_author else 0
    creator_len = len(str(creator).strip()) if has_creator else 0
    producer_len = len(str(producer).strip()) if has_producer else 0

    # Keyword count
    if has_keywords:
        kw_str = str(keywords)
        # Split by comma or semicolon
        kw_parts = [k.strip() for k in kw_str.replace(";", ",").split(",") if k.strip()]
        keyword_count = max(len(kw_parts), 1)
    else:
        keyword_count = 0

    creation_year = parse_year_from_iso(created_at) if has_creation_date else 0
    modification_year = parse_year_from_iso(modified_at) if has_modification_date else 0
    age_days = calculate_age_days(created_at) if has_creation_date else -1.0

    # Modified after created check (factual)
    modified_after_created = False
    if has_creation_date and has_modification_date:
        try:
            dt_create = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
            dt_mod = datetime.fromisoformat(str(modified_at).replace("Z", "+00:00"))
            modified_after_created = dt_mod > dt_create
        except Exception:
            modified_after_created = False

    # ── Section 9: Metadata Consistency ────────────────────────────────────
    author_equals_lmb = False
    if has_author and has_last_modified_by:
        author_equals_lmb = str(author).strip().lower() == str(last_modified_by).strip().lower()

    creator_and_producer = has_creator and has_producer
    both_dates_present = has_creation_date and has_modification_date

    field_count = sum([
        has_title,
        has_author,
        has_subject,
        has_creator,
        has_producer,
        has_keywords,
        has_creation_date,
        has_modification_date,
        has_last_modified_by,
    ])
    completeness_ratio = round(field_count / float(len(EXPECTED_FIELDS)), 4)

    return {
        # Section 8: Metadata existence & lengths
        "has_title": has_title,
        "has_author": has_author,
        "has_subject": has_subject,
        "has_creator": has_creator,
        "has_producer": has_producer,
        "has_keywords": has_keywords,
        "has_creation_date": has_creation_date,
        "has_modification_date": has_modification_date,
        "has_last_modified_by": has_last_modified_by,
        "title_length": title_len,
        "author_length": author_len,
        "creator_length": creator_len,
        "producer_length": producer_len,
        "keyword_count": keyword_count,
        "metadata_creation_year": creation_year,
        "metadata_modification_year": modification_year,
        "metadata_age_days": age_days,
        "metadata_modified_after_created": modified_after_created,

        # Section 9: Metadata consistency
        "author_equals_last_modified_by": author_equals_lmb,
        "creator_present_and_producer_present": creator_and_producer,
        "creation_date_present_and_modification_date_present": both_dates_present,
        "metadata_field_count": field_count,
        "metadata_completeness_ratio": completeness_ratio,
    }
