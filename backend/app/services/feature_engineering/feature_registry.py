"""
Central Feature Registry for version 1.0.
Maintains deterministic catalog of all feature definitions, types, categories,
descriptions, sources, default values, and ordering.
"""
from typing import Dict, List, Optional
from app.services.feature_engineering.exceptions import FeatureRegistryError
from app.services.feature_engineering.feature_schema import FeatureDefinition


class FeatureRegistry:
    """
    Singleton-style centralized feature registry.
    Ensures consistent names, types, descriptions, and deterministic feature vector ordering.
    """

    def __init__(self):
        self._features: Dict[str, FeatureDefinition] = {}
        self._ordered_keys: List[str] = []
        self._init_v1_features()

    def register(self, feature_def: FeatureDefinition) -> None:
        """Register a new feature definition."""
        if feature_def.name in self._features:
            raise FeatureRegistryError(f"Feature '{feature_def.name}' is already registered.")
        self._features[feature_def.name] = feature_def
        self._ordered_keys.append(feature_def.name)

    def get(self, name: str) -> FeatureDefinition:
        """Retrieve definition for a feature name."""
        if name not in self._features:
            raise FeatureRegistryError(f"Feature '{name}' not found in registry.")
        return self._features[name]

    def list_features(self, category: Optional[str] = None) -> List[FeatureDefinition]:
        """List features optionally filtered by category."""
        if category:
            return [f for f in self._features.values() if f.category == category]
        return list(self._features.values())

    def get_feature_names(self) -> List[str]:
        """Return deterministic ordered list of all feature names."""
        return list(self._ordered_keys)

    def get_feature_count(self) -> int:
        """Return total number of registered features."""
        return len(self._features)

    def to_dict(self) -> Dict[str, Dict]:
        """Export registry as dictionary for documentation / API introspection."""
        return {k: v.to_dict() for k, v in self._features.items()}

    def _init_v1_features(self):
        """Populate Feature Registry v1.0 specifications."""
        definitions: List[FeatureDefinition] = [
            # ── 1. File-Level Features (Section 4) ──────────────────────────
            FeatureDefinition("file_size_bytes", "file", "integer", "File size in raw bytes", "file_metadata", default_value=0),
            FeatureDefinition("file_size_kb", "file", "float", "File size in kilobytes", "file_metadata", default_value=0.0),
            FeatureDefinition("file_size_mb", "file", "float", "File size in megabytes", "file_metadata", default_value=0.0),
            FeatureDefinition("file_extension_code", "file", "integer", "Deterministic categorical code for extension (1=pdf, 2=docx, 3=doc, 4=jpg, 5=png, 0=other)", "file_metadata", default_value=0),
            FeatureDefinition("mime_type_code", "file", "integer", "Deterministic categorical code for MIME type", "file_metadata", default_value=0),
            FeatureDefinition("has_hash", "file", "boolean", "Whether original file has computed hash", "file_metadata", default_value=False),
            FeatureDefinition("filename_length", "file", "integer", "Character length of original filename", "file_metadata", default_value=0),
            FeatureDefinition("filename_digit_count", "file", "integer", "Count of digits in original filename", "file_metadata", default_value=0),
            FeatureDefinition("filename_special_character_count", "file", "integer", "Count of special characters in original filename", "file_metadata", default_value=0),
            FeatureDefinition("filename_has_uuid_pattern", "file", "boolean", "Whether filename contains UUID hexadecimal pattern", "file_metadata", default_value=False),

            # ── 2. Text Features (Section 5) ─────────────────────────────────
            FeatureDefinition("character_count", "text", "integer", "Total character count of cleaned text", "clean_text", default_value=0),
            FeatureDefinition("word_count", "text", "integer", "Total word token count of cleaned text", "clean_text", default_value=0),
            FeatureDefinition("sentence_count", "text", "integer", "Estimated total sentence count", "clean_text", default_value=0),
            FeatureDefinition("paragraph_count", "text", "integer", "Total paragraph count", "clean_text", default_value=0),
            FeatureDefinition("average_word_length", "text", "float", "Average character length of words", "clean_text", default_value=0.0),
            FeatureDefinition("average_sentence_length", "text", "float", "Average word count per sentence", "clean_text", default_value=0.0),
            FeatureDefinition("numeric_token_count", "text", "integer", "Count of tokens composed purely of numbers", "clean_text", default_value=0),
            FeatureDefinition("uppercase_character_count", "text", "integer", "Count of uppercase alphabetic characters", "clean_text", default_value=0),
            FeatureDefinition("lowercase_character_count", "text", "integer", "Count of lowercase alphabetic characters", "clean_text", default_value=0),
            FeatureDefinition("punctuation_count", "text", "integer", "Count of punctuation characters", "clean_text", default_value=0),
            FeatureDefinition("whitespace_count", "text", "integer", "Count of whitespace characters", "clean_text", default_value=0),
            FeatureDefinition("digit_count", "text", "integer", "Count of decimal digit characters", "clean_text", default_value=0),
            FeatureDefinition("alphabetic_character_count", "text", "integer", "Count of alphabetic characters", "clean_text", default_value=0),
            FeatureDefinition("unique_word_count", "text", "integer", "Count of unique lowercase word tokens", "clean_text", default_value=0),
            FeatureDefinition("vocabulary_richness", "text", "float", "Ratio of unique words to total words (0.0 if empty)", "clean_text", default_value=0.0),

            # ── 3. Text Quality Features (Section 6) ─────────────────────────
            FeatureDefinition("empty_text_ratio", "text_quality", "float", "Ratio of empty lines to total lines", "clean_text", default_value=0.0),
            FeatureDefinition("numeric_ratio", "text_quality", "float", "Ratio of numeric tokens to total tokens", "clean_text", default_value=0.0),
            FeatureDefinition("uppercase_ratio", "text_quality", "float", "Ratio of uppercase characters to total characters", "clean_text", default_value=0.0),
            FeatureDefinition("punctuation_ratio", "text_quality", "float", "Ratio of punctuation characters to total characters", "clean_text", default_value=0.0),
            FeatureDefinition("digit_ratio", "text_quality", "float", "Ratio of digit characters to total characters", "clean_text", default_value=0.0),
            FeatureDefinition("repeated_line_ratio", "text_quality", "float", "Ratio of non-unique lines to total lines", "clean_text", default_value=0.0),
            FeatureDefinition("repeated_token_ratio", "text_quality", "float", "Ratio of consecutive identical tokens", "clean_text", default_value=0.0),
            FeatureDefinition("short_line_ratio", "text_quality", "float", "Ratio of lines shorter than 10 characters", "clean_text", default_value=0.0),
            FeatureDefinition("long_line_ratio", "text_quality", "float", "Ratio of lines longer than 120 characters", "clean_text", default_value=0.0),
            FeatureDefinition("has_fragmented_words", "text_quality", "boolean", "Presence of fragmented word artifacts", "clean_text", default_value=False),
            FeatureDefinition("abnormal_whitespace_ratio", "text_quality", "float", "Ratio of irregular spacing patterns", "clean_text", default_value=0.0),
            FeatureDefinition("repeated_char_max_streak", "text_quality", "integer", "Maximum streak of identical consecutive characters", "clean_text", default_value=0),
            FeatureDefinition("encoding_artifact_count", "text_quality", "integer", "Count of unusual replacement or encoding symbols", "clean_text", default_value=0),

            # ── 4. Date and Numeric Features (Section 7) ─────────────────────
            FeatureDefinition("detected_date_count", "date_numeric", "integer", "Number of generic dates detected in text", "clean_text", default_value=0),
            FeatureDefinition("detected_year_count", "date_numeric", "integer", "Number of 4-digit calendar years detected", "clean_text", default_value=0),
            FeatureDefinition("detected_numeric_value_count", "date_numeric", "integer", "Number of currency, decimal, or ID numbers detected", "clean_text", default_value=0),
            FeatureDefinition("earliest_detected_year", "date_numeric", "integer", "Earliest 4-digit calendar year found in text (0 if none)", "clean_text", default_value=0),
            FeatureDefinition("latest_detected_year", "date_numeric", "integer", "Latest 4-digit calendar year found in text (0 if none)", "clean_text", default_value=0),
            FeatureDefinition("date_format_count", "date_numeric", "integer", "Count of distinct date formatting syntaxes found", "clean_text", default_value=0),

            # ── 5. Metadata Features (Section 8) ─────────────────────────────
            FeatureDefinition("has_title", "metadata", "boolean", "Whether title is present in metadata", "standardized_metadata", default_value=False),
            FeatureDefinition("has_author", "metadata", "boolean", "Whether author is present in metadata", "standardized_metadata", default_value=False),
            FeatureDefinition("has_subject", "metadata", "boolean", "Whether subject is present in metadata", "standardized_metadata", default_value=False),
            FeatureDefinition("has_creator", "metadata", "boolean", "Whether creator software is present in metadata", "standardized_metadata", default_value=False),
            FeatureDefinition("has_producer", "metadata", "boolean", "Whether producer is present in metadata", "standardized_metadata", default_value=False),
            FeatureDefinition("has_keywords", "metadata", "boolean", "Whether keywords are present in metadata", "standardized_metadata", default_value=False),
            FeatureDefinition("has_creation_date", "metadata", "boolean", "Whether creation date is present in metadata", "standardized_metadata", default_value=False),
            FeatureDefinition("has_modification_date", "metadata", "boolean", "Whether modification date is present in metadata", "standardized_metadata", default_value=False),
            FeatureDefinition("has_last_modified_by", "metadata", "boolean", "Whether last modified by is present in metadata", "standardized_metadata", default_value=False),
            FeatureDefinition("title_length", "metadata", "integer", "Length of title string", "standardized_metadata", default_value=0),
            FeatureDefinition("author_length", "metadata", "integer", "Length of author string", "standardized_metadata", default_value=0),
            FeatureDefinition("creator_length", "metadata", "integer", "Length of creator string", "standardized_metadata", default_value=0),
            FeatureDefinition("producer_length", "metadata", "integer", "Length of producer string", "standardized_metadata", default_value=0),
            FeatureDefinition("keyword_count", "metadata", "integer", "Count of keywords/tags in metadata", "standardized_metadata", default_value=0),
            FeatureDefinition("metadata_creation_year", "metadata", "integer", "Calendar year of metadata creation date (0 if none)", "standardized_metadata", default_value=0),
            FeatureDefinition("metadata_modification_year", "metadata", "integer", "Calendar year of metadata modification date (0 if none)", "standardized_metadata", default_value=0),
            FeatureDefinition("metadata_age_days", "metadata", "float", "Days between creation date and today (-1.0 if unknown)", "standardized_metadata", default_value=-1.0),
            FeatureDefinition("metadata_modified_after_created", "metadata", "boolean", "Factual indicator: modification date > creation date", "standardized_metadata", default_value=False),

            # ── 6. Metadata Consistency Features (Section 9) ─────────────────
            FeatureDefinition("author_equals_last_modified_by", "metadata_consistency", "boolean", "Author and last_modified_by strings match identically", "metadata_consistency", default_value=False),
            FeatureDefinition("creator_present_and_producer_present", "metadata_consistency", "boolean", "Both creator and producer fields are non-empty", "metadata_consistency", default_value=False),
            FeatureDefinition("creation_date_present_and_modification_date_present", "metadata_consistency", "boolean", "Both creation and modification dates are non-empty", "metadata_consistency", default_value=False),
            FeatureDefinition("metadata_field_count", "metadata_consistency", "integer", "Total number of non-null metadata fields", "metadata_consistency", default_value=0),
            FeatureDefinition("metadata_completeness_ratio", "metadata_consistency", "float", "Ratio of present fields to expected fields (out of 9)", "metadata_consistency", default_value=0.0),

            # ── 7. PDF Structural Features (Section 10) ──────────────────────
            FeatureDefinition("page_count", "structural", "integer", "Total number of pages", "structural_analysis", default_value=1),
            FeatureDefinition("image_count", "structural", "integer", "Total embedded images count", "structural_analysis", default_value=0),
            FeatureDefinition("link_count", "structural", "integer", "Total hyperlinks count", "structural_analysis", default_value=0),
            FeatureDefinition("text_block_count", "structural", "integer", "Total text layout blocks count", "structural_analysis", default_value=0),
            FeatureDefinition("average_text_blocks_per_page", "structural", "float", "Mean text blocks per page", "structural_analysis", default_value=0.0),
            FeatureDefinition("average_images_per_page", "structural", "float", "Mean embedded images per page", "structural_analysis", default_value=0.0),
            FeatureDefinition("pages_with_images_count", "structural", "integer", "Count of pages containing at least one image", "structural_analysis", default_value=0),
            FeatureDefinition("pages_with_no_text_count", "structural", "integer", "Count of pages containing zero text characters", "structural_analysis", default_value=0),
            FeatureDefinition("pages_with_text_count", "structural", "integer", "Count of pages containing extractable text", "structural_analysis", default_value=0),
            FeatureDefinition("text_page_ratio", "structural", "float", "Ratio of pages with text to total pages", "structural_analysis", default_value=0.0),
            FeatureDefinition("image_only_page_ratio", "structural", "float", "Ratio of pages containing only images without text", "structural_analysis", default_value=0.0),
            FeatureDefinition("unique_font_count", "structural", "integer", "Count of distinct font families detected", "structural_analysis", default_value=0),
            FeatureDefinition("font_name_count", "structural", "integer", "Count of distinct font variant names", "structural_analysis", default_value=0),
            FeatureDefinition("minimum_font_size", "structural", "float", "Minimum font size in points", "structural_analysis", default_value=0.0),
            FeatureDefinition("maximum_font_size", "structural", "float", "Maximum font size in points", "structural_analysis", default_value=0.0),
            FeatureDefinition("average_font_size", "structural", "float", "Mean font size in points", "structural_analysis", default_value=0.0),
            FeatureDefinition("font_size_std", "structural", "float", "Standard deviation of font sizes", "structural_analysis", default_value=0.0),
            FeatureDefinition("unique_page_width_count", "structural", "integer", "Number of distinct page widths", "structural_analysis", default_value=0),
            FeatureDefinition("unique_page_height_count", "structural", "integer", "Number of distinct page heights", "structural_analysis", default_value=0),
            FeatureDefinition("page_dimension_consistency_ratio", "structural", "float", "Ratio of modal page dimensions to total pages", "structural_analysis", default_value=1.0),

            # ── 8. DOCX Structural Features (Section 11) ─────────────────────
            FeatureDefinition("docx_paragraph_count", "structural", "integer", "DOCX paragraph count", "structural_analysis", default_value=0),
            FeatureDefinition("docx_heading_count", "structural", "integer", "DOCX heading count", "structural_analysis", default_value=0),
            FeatureDefinition("docx_table_count", "structural", "integer", "DOCX table count", "structural_analysis", default_value=0),
            FeatureDefinition("docx_image_count", "structural", "integer", "DOCX image count", "structural_analysis", default_value=0),
            FeatureDefinition("docx_hyperlink_count", "structural", "integer", "DOCX hyperlink count", "structural_analysis", default_value=0),
            FeatureDefinition("docx_section_count", "structural", "integer", "DOCX section count", "structural_analysis", default_value=0),
            FeatureDefinition("average_paragraph_length", "structural", "float", "Mean character length of paragraphs", "structural_analysis", default_value=0.0),
            FeatureDefinition("average_heading_length", "structural", "float", "Mean character length of headings", "structural_analysis", default_value=0.0),
            FeatureDefinition("table_to_paragraph_ratio", "structural", "float", "Ratio of tables to paragraphs", "structural_analysis", default_value=0.0),
            FeatureDefinition("image_to_paragraph_ratio", "structural", "float", "Ratio of images to paragraphs", "structural_analysis", default_value=0.0),

            # ── 9. Image Features (Section 12) ───────────────────────────────
            FeatureDefinition("image_width", "image", "integer", "Image width in pixels", "image_structure", default_value=0),
            FeatureDefinition("image_height", "image", "integer", "Image height in pixels", "image_structure", default_value=0),
            FeatureDefinition("image_aspect_ratio", "image", "float", "Width divided by height", "image_structure", default_value=0.0),
            FeatureDefinition("image_pixel_count", "image", "integer", "Total pixels (width * height)", "image_structure", default_value=0),
            FeatureDefinition("image_color_mode_code", "image", "integer", "Deterministic code for color mode (1=RGB, 2=RGBA, 3=L, 4=CMYK, 0=other)", "image_structure", default_value=0),
            FeatureDefinition("has_exif", "image", "boolean", "Whether EXIF metadata is present", "image_structure", default_value=False),
            FeatureDefinition("exif_field_count", "image", "integer", "Number of present EXIF tags", "image_structure", default_value=0),
            FeatureDefinition("image_format_code", "image", "integer", "Deterministic code for image format (1=JPEG, 2=PNG, 3=TIFF, 4=BMP, 0=other)", "image_structure", default_value=0),
            FeatureDefinition("resolution_category_code", "image", "integer", "Resolution category (1=low, 2=standard, 3=high, 4=ultra-high, 0=none)", "image_structure", default_value=0),

            # ── 10. Cross-Source Consistency & Missingness (Sections 13 & 15) 
            FeatureDefinition("text_page_count_vs_structural_page_count", "cross_source", "float", "Difference ratio between text pages and structural pages", "cross_source", default_value=0.0),
            FeatureDefinition("paragraph_count_consistency", "cross_source", "float", "Consistency between text paragraph count and structural paragraph count", "cross_source", default_value=1.0),
            FeatureDefinition("image_count_consistency", "cross_source", "float", "Consistency between extracted image count and structural images", "cross_source", default_value=1.0),
            FeatureDefinition("metadata_date_consistency", "cross_source", "boolean", "Whether creation date <= modification date when both exist", "cross_source", default_value=True),
            FeatureDefinition("document_text_present", "cross_source", "boolean", "Whether document yielded extractable text", "cross_source", default_value=False),
            FeatureDefinition("document_metadata_present", "cross_source", "boolean", "Whether document yielded any metadata", "cross_source", default_value=False),
            FeatureDefinition("document_structure_present", "cross_source", "boolean", "Whether document yielded structural data", "cross_source", default_value=False),
            FeatureDefinition("metadata_missing", "cross_source", "boolean", "Indicator: all metadata fields are null", "missingness", default_value=False),
            FeatureDefinition("structural_data_missing", "cross_source", "boolean", "Indicator: structural data block is empty", "missingness", default_value=False),
            FeatureDefinition("text_missing", "cross_source", "boolean", "Indicator: extracted text is empty", "missingness", default_value=False),
            FeatureDefinition("ocr_data_missing", "cross_source", "boolean", "Indicator: OCR was required but unavailable or failed", "missingness", default_value=False),
            FeatureDefinition("ocr_used", "cross_source", "boolean", "Whether OCR was executed", "cross_source", default_value=False),
            FeatureDefinition("ocr_status_code", "cross_source", "integer", "OCR status code (0=not_required, 1=completed, 2=unavailable, 3=failed)", "cross_source", default_value=0),

            # ── 11. Integrity Features (Section 14) ──────────────────────────
            FeatureDefinition("sha256_present", "integrity", "boolean", "Whether SHA-256 fingerprint is present", "integrity", default_value=False),
            FeatureDefinition("hash_length", "integrity", "integer", "Length of the file hash string (64 for SHA-256)", "integrity", default_value=0),
            FeatureDefinition("hash_algorithm_code", "integrity", "integer", "Algorithm code (1=SHA-256, 0=none/unknown)", "integrity", default_value=0),
        ]

        for defn in definitions:
            self.register(defn)


# Global singleton instance
feature_registry = FeatureRegistry()
