"""
Text, lexical diversity, text quality, and generic date/numeric feature extractor.
Processes cleaned text produced by Phase 2. Handles empty documents safely.
"""
import re
import string
from typing import Any, Dict, List, Set, Tuple


# Generic date patterns across global formats (ISO, European, American, Alpha-month)
DATE_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b"),                # 2024-05-12, 2024/05/12
    re.compile(r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b"),             # 12/05/2024, 05-12-2024
    re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b", re.IGNORECASE),  # October 1, 2024
    re.compile(r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b", re.IGNORECASE),  # 1 October 2024
]

YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")
NUMERIC_VALUE_PATTERN = re.compile(r"\b[$€£₹¥]?\d+(?:,\d{3})*(?:\.\d+)?%?\b")


def extract_text_features(cleaned_text: str | None) -> Dict[str, Any]:
    """
    Extract text metrics, text quality ratios, and date/numeric features.
    Guaranteed deterministic and safe for empty/sparse texts.
    """
    text = (cleaned_text or "").strip()

    if not text:
        return _empty_text_features()

    total_chars = len(text)
    words = text.split()
    total_words = len(words)

    # Paragraphs (blocks separated by 2+ newlines or single non-empty lines)
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    paragraph_count = max(len(paragraphs), 1 if total_words > 0 else 0)

    # Sentences (split by ., !, ?, considering whitespace)
    sentences = [s.strip() for s in re.split(r"[.!?]+(?:\s+|$)", text) if s.strip()]
    sentence_count = max(len(sentences), 1 if total_words > 0 else 0)

    # Character level distributions
    uppercase_count = sum(1 for c in text if c.isupper())
    lowercase_count = sum(1 for c in text if c.islower())
    digit_count = sum(1 for c in text if c.isdigit())
    alpha_count = sum(1 for c in text if c.isalpha())
    whitespace_count = sum(1 for c in text if c.isspace())
    punctuation_count = sum(1 for c in text if c in string.punctuation)

    # Word level metrics
    word_lengths = [len(w) for w in words]
    average_word_length = round(sum(word_lengths) / total_words, 3) if total_words > 0 else 0.0
    average_sentence_length = round(total_words / sentence_count, 3) if sentence_count > 0 else 0.0

    numeric_tokens = [w for w in words if re.match(r"^\d+(?:\.\d+)?$", w)]
    numeric_token_count = len(numeric_tokens)

    # Vocabulary richness
    clean_word_tokens = [w.strip(string.punctuation).lower() for w in words if w.strip(string.punctuation)]
    unique_words = set(clean_word_tokens)
    unique_word_count = len(unique_words)
    vocabulary_richness = round(unique_word_count / total_words, 4) if total_words > 0 else 0.0

    # ── Text Quality & Ratios ──────────────────────────────────────────────
    lines = text.split("\n")
    total_lines = max(len(lines), 1)
    empty_lines = sum(1 for l in lines if not l.strip())
    empty_text_ratio = round(empty_lines / total_lines, 4)

    numeric_ratio = round(numeric_token_count / total_words, 4) if total_words > 0 else 0.0
    uppercase_ratio = round(uppercase_count / total_chars, 4) if total_chars > 0 else 0.0
    punctuation_ratio = round(punctuation_count / total_chars, 4) if total_chars > 0 else 0.0
    digit_ratio = round(digit_count / total_chars, 4) if total_chars > 0 else 0.0

    non_empty_lines = [l.strip() for l in lines if l.strip()]
    unique_lines = set(non_empty_lines)
    repeated_line_ratio = round((len(non_empty_lines) - len(unique_lines)) / max(len(non_empty_lines), 1), 4) if non_empty_lines else 0.0

    # Consecutive repeated tokens
    repeated_tokens = 0
    for i in range(1, len(words)):
        if words[i].lower() == words[i - 1].lower():
            repeated_tokens += 1
    repeated_token_ratio = round(repeated_tokens / total_words, 4) if total_words > 0 else 0.0

    short_lines = sum(1 for l in non_empty_lines if len(l) < 10)
    long_lines = sum(1 for l in non_empty_lines if len(l) > 120)
    short_line_ratio = round(short_lines / max(len(non_empty_lines), 1), 4) if non_empty_lines else 0.0
    long_line_ratio = round(long_lines / max(len(non_empty_lines), 1), 4) if non_empty_lines else 0.0

    # Extraction artifacts
    # Fragmented words (e.g. sequences of single characters like "d e p a r t m e n t")
    has_fragmented_words = bool(re.search(r"\b(?:[a-zA-Z]\s){4,}[a-zA-Z]\b", text))

    # Abnormal whitespace ratio
    abnormal_ws_count = len(re.findall(r"[ \t]{3,}", text))
    abnormal_whitespace_ratio = round(abnormal_ws_count / total_lines, 4)

    # Repeated char streak (e.g. "aaaaa" or "------")
    streaks = [len(m.group(0)) for m in re.finditer(r"(.)\1{2,}", text)]
    max_streak = max(streaks) if streaks else 0

    # Suspicious encoding symbols (replacement character, control remnants)
    encoding_artifacts = len(re.findall(r"[\ufffd\u0000-\u0008\u000b\u000c\u000e-\u001f]", text))

    # ── Date and Numeric Features ──────────────────────────────────────────
    dates_found = []
    distinct_formats_seen: Set[int] = set()
    for idx, pat in enumerate(DATE_PATTERNS):
        matches = pat.findall(text)
        if matches:
            dates_found.extend(matches)
            distinct_formats_seen.add(idx)

    detected_date_count = len(dates_found)
    date_format_count = len(distinct_formats_seen)

    years_found = [int(y) for y in YEAR_PATTERN.findall(text)]
    detected_year_count = len(years_found)
    earliest_year = min(years_found) if years_found else 0
    latest_year = max(years_found) if years_found else 0

    numeric_vals = NUMERIC_VALUE_PATTERN.findall(text)
    detected_numeric_value_count = len(numeric_vals)

    return {
        # Section 5: Text features
        "character_count": total_chars,
        "word_count": total_words,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "average_word_length": average_word_length,
        "average_sentence_length": average_sentence_length,
        "numeric_token_count": numeric_token_count,
        "uppercase_character_count": uppercase_count,
        "lowercase_character_count": lowercase_count,
        "punctuation_count": punctuation_count,
        "whitespace_count": whitespace_count,
        "digit_count": digit_count,
        "alphabetic_character_count": alpha_count,
        "unique_word_count": unique_word_count,
        "vocabulary_richness": vocabulary_richness,

        # Section 6: Text quality
        "empty_text_ratio": empty_text_ratio,
        "numeric_ratio": numeric_ratio,
        "uppercase_ratio": uppercase_ratio,
        "punctuation_ratio": punctuation_ratio,
        "digit_ratio": digit_ratio,
        "repeated_line_ratio": repeated_line_ratio,
        "repeated_token_ratio": repeated_token_ratio,
        "short_line_ratio": short_line_ratio,
        "long_line_ratio": long_line_ratio,
        "has_fragmented_words": has_fragmented_words,
        "abnormal_whitespace_ratio": abnormal_whitespace_ratio,
        "repeated_char_max_streak": max_streak,
        "encoding_artifact_count": encoding_artifacts,

        # Section 7: Dates and Numerics
        "detected_date_count": detected_date_count,
        "detected_year_count": detected_year_count,
        "detected_numeric_value_count": detected_numeric_value_count,
        "earliest_detected_year": earliest_year,
        "latest_detected_year": latest_year,
        "date_format_count": date_format_count,
    }


def _empty_text_features() -> Dict[str, Any]:
    """Default values when document text is empty."""
    return {
        "character_count": 0,
        "word_count": 0,
        "sentence_count": 0,
        "paragraph_count": 0,
        "average_word_length": 0.0,
        "average_sentence_length": 0.0,
        "numeric_token_count": 0,
        "uppercase_character_count": 0,
        "lowercase_character_count": 0,
        "punctuation_count": 0,
        "whitespace_count": 0,
        "digit_count": 0,
        "alphabetic_character_count": 0,
        "unique_word_count": 0,
        "vocabulary_richness": 0.0,
        "empty_text_ratio": 1.0,
        "numeric_ratio": 0.0,
        "uppercase_ratio": 0.0,
        "punctuation_ratio": 0.0,
        "digit_ratio": 0.0,
        "repeated_line_ratio": 0.0,
        "repeated_token_ratio": 0.0,
        "short_line_ratio": 0.0,
        "long_line_ratio": 0.0,
        "has_fragmented_words": False,
        "abnormal_whitespace_ratio": 0.0,
        "repeated_char_max_streak": 0,
        "encoding_artifact_count": 0,
        "detected_date_count": 0,
        "detected_year_count": 0,
        "detected_numeric_value_count": 0,
        "earliest_detected_year": 0,
        "latest_detected_year": 0,
        "date_format_count": 0,
    }
