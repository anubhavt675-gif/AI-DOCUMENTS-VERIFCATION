"""
Text normalization and cleaning pipeline.
Preserves numbers, punctuation, dates, document IDs, section numbers,
monetary values, and government codes for downstream ML anomaly detection.
"""
import re
import unicodedata
from typing import Tuple

from app.services.document_processing.models import TextExtractionResult


def clean_text(raw_text: str) -> str:
    """
    Normalize and clean raw extracted text:
    1. Unicode normalization (NFKC decomposes compatibility chars & resolves ligatures like 'fi', 'fl')
    2. Normalize line endings (\\r\\n and \\r to \\n)
    3. Replace soft hyphens, zero-width chars, and non-breaking spaces
    4. Strip non-printable control characters (while retaining \\n, \\t)
    5. Clean up PDF hyphenation at line breaks (e.g., 'govern-\\nment' -> 'government')
    6. Normalize multiple horizontal whitespace into a single space
    7. Normalize excessive line breaks (max 2 consecutive newlines)
    8. Preserve punctuation, numbers, and structural casing
    """
    if not raw_text:
        return ""

    # 1. Unicode normalization (NFKC)
    text = unicodedata.normalize("NFKC", raw_text)

    # 2. Line ending normalization
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Safe normalization of common PDF artifacts
    text = text.replace("\u00a0", " ")   # non-breaking space
    text = text.replace("\u200b", "")    # zero-width space
    text = text.replace("\u200c", "")    # zero-width non-joiner
    text = text.replace("\u200d", "")    # zero-width joiner
    text = text.replace("\u200e", "")    # LTR mark
    text = text.replace("\u200f", "")    # RTL mark
    text = text.replace("\ufeff", "")    # BOM
    text = text.replace("\u00ad", "")    # soft hyphen

    # 4. Strip control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # 5. Fix hyphenation at line breaks (e.g. 'depart-\nment' -> 'department')
    text = re.sub(r"(\b[A-Za-z]+)-\n([a-z]+\b)", r"\1\2", text)

    # 6. Normalize horizontal whitespace per line
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
        cleaned_lines.append(cleaned_line)

    text = "\n".join(cleaned_lines)

    # 7. Normalize multiple empty lines to at most 2 newlines (paragraph separator)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def process_text_extraction(raw_text: str) -> TextExtractionResult:
    """
    Takes raw text, cleans it, calculates word, character, and paragraph counts.
    """
    cleaned = clean_text(raw_text)
    words = cleaned.split() if cleaned else []
    word_count = len(words)
    character_count = len(cleaned)

    # Estimate paragraphs (non-empty blocks separated by double newlines or single newlines with content)
    if not cleaned:
        paragraph_count = 0
    else:
        paragraphs = [p for p in re.split(r"\n\s*\n", cleaned) if p.strip()]
        paragraph_count = max(len(paragraphs), 1 if word_count > 0 else 0)

    return TextExtractionResult(
        raw_text=raw_text,
        cleaned_text=cleaned,
        word_count=word_count,
        character_count=character_count,
        paragraph_count=paragraph_count,
    )
