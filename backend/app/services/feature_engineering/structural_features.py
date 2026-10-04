"""
Structural feature extractor for PDF, DOCX, and Image documents.
Extracts geometry, typography, embedded structures, and format-specific attributes.
"""
import math
from typing import Any, Dict, List, Optional


COLOR_MODE_MAP = {"RGB": 1, "RGBA": 2, "L": 3, "CMYK": 4}
IMAGE_FORMAT_MAP = {"JPEG": 1, "JPG": 1, "PNG": 2, "TIFF": 3, "BMP": 4}


def extract_structural_features(
    structure: Optional[Dict[str, Any]],
    raw_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract structural metrics across PDF, DOCX, and Images.
    Fills appropriate format features and sets sensible defaults for non-applicable features.
    """
    struct = structure or {}
    fmt = (struct.get("format") or "").upper()

    # ── PDF Structural Features ──────────────────────────────────────────────
    page_count = int(struct.get("page_count") or 1)
    img_count = int(struct.get("total_images") or struct.get("image_count") or 0)
    link_count = int(struct.get("total_links") or 0)
    text_block_count = int(struct.get("total_text_blocks") or 0)

    avg_blocks_per_page = round(text_block_count / float(page_count), 2) if page_count > 0 else 0.0
    avg_images_per_page = round(img_count / float(page_count), 2) if page_count > 0 else 0.0

    low_text_pages = struct.get("pages_with_low_text") or []
    image_only_pages = struct.get("pages_with_only_images") or []
    image_only_page_ratio = round(len(image_only_pages) / float(page_count), 4) if page_count > 0 else 0.0

    # Pages with text vs no text
    no_text_count = len(image_only_pages)
    text_page_count = max(0, page_count - no_text_count)
    text_page_ratio = round(text_page_count / float(page_count), 4) if page_count > 0 else 1.0

    # Font features
    font_names = struct.get("font_names") or []
    unique_font_count = len(font_names)
    font_name_count = int(struct.get("font_count") or len(font_names))

    font_size_range = struct.get("font_size_range") or {}
    min_font_size = float(font_size_range.get("min", 0.0))
    max_font_size = float(font_size_range.get("max", 0.0))
    avg_font_size = round((min_font_size + max_font_size) / 2.0, 2) if (min_font_size > 0 or max_font_size > 0) else 0.0
    font_size_std = round(abs(max_font_size - min_font_size) / 2.0, 2) if max_font_size > min_font_size else 0.0

    # Page dimension consistency
    page_dimensions = struct.get("page_dimensions") or []
    widths = [p.get("width") for p in page_dimensions if p.get("width")]
    heights = [p.get("height") for p in page_dimensions if p.get("height")]
    unique_width_count = len(set(widths)) if widths else 0
    unique_height_count = len(set(heights)) if heights else 0
    dim_consistency = 1.0
    if page_dimensions:
        # Check modal dimensions
        dim_tuples = [(round(p.get("width", 0), 1), round(p.get("height", 0), 1)) for p in page_dimensions]
        if dim_tuples:
            from collections import Counter
            counts = Counter(dim_tuples)
            modal_count = counts.most_common(1)[0][1]
            dim_consistency = round(modal_count / float(len(dim_tuples)), 4)

    # ── DOCX Structural Features ─────────────────────────────────────────────
    docx_p_count = int(struct.get("paragraph_count") or 0)
    docx_h_count = int(struct.get("heading_count") or 0)
    docx_t_count = int(struct.get("table_count") or 0)
    docx_img_count = int(struct.get("image_count") or 0)
    docx_link_count = int(struct.get("hyperlink_count") or 0)
    docx_sec_count = int(struct.get("section_count") or 0)

    # Paragraph and heading lengths
    headings = struct.get("headings") or []
    avg_heading_len = round(sum(len(h) for h in headings) / float(len(headings)), 2) if headings else 0.0

    raw_len = len(raw_text or "")
    avg_p_len = round(raw_len / float(docx_p_count), 2) if docx_p_count > 0 else 0.0

    table_to_p_ratio = round(docx_t_count / float(docx_p_count), 4) if docx_p_count > 0 else 0.0
    img_to_p_ratio = round(docx_img_count / float(docx_p_count), 4) if docx_p_count > 0 else 0.0

    # ── Image Features ───────────────────────────────────────────────────────
    img_w = int(struct.get("width") or 0)
    img_h = int(struct.get("height") or 0)
    aspect_ratio = float(struct.get("aspect_ratio") or (round(img_w / float(img_h), 3) if img_h > 0 else 0.0))
    pixel_count = img_w * img_h

    color_mode = (struct.get("color_mode") or "").upper()
    color_mode_code = COLOR_MODE_MAP.get(color_mode, 0 if not color_mode else 9)

    has_exif = bool(struct.get("has_exif") or False)
    exif_count = 1 if has_exif else 0

    img_format = fmt if fmt in ("JPEG", "JPG", "PNG", "TIFF", "BMP") else ""
    image_format_code = IMAGE_FORMAT_MAP.get(img_format, 0)

    # Resolution category: 1=low (<0.5MP), 2=standard (0.5-2MP), 3=high (2-8MP), 4=ultra-high (>8MP)
    if pixel_count == 0:
        resolution_cat = 0
    elif pixel_count < 500_000:
        resolution_cat = 1
    elif pixel_count < 2_000_000:
        resolution_cat = 2
    elif pixel_count < 8_000_000:
        resolution_cat = 3
    else:
        resolution_cat = 4

    return {
        # Section 10: PDF structural
        "page_count": page_count,
        "image_count": img_count,
        "link_count": link_count,
        "text_block_count": text_block_count,
        "average_text_blocks_per_page": avg_blocks_per_page,
        "average_images_per_page": avg_images_per_page,
        "pages_with_images_count": 1 if img_count > 0 and page_count == 1 else (page_count if img_count > 0 else 0),
        "pages_with_no_text_count": no_text_count,
        "pages_with_text_count": text_page_count,
        "text_page_ratio": text_page_ratio,
        "image_only_page_ratio": image_only_page_ratio,
        "unique_font_count": unique_font_count,
        "font_name_count": font_name_count,
        "minimum_font_size": min_font_size,
        "maximum_font_size": max_font_size,
        "average_font_size": avg_font_size,
        "font_size_std": font_size_std,
        "unique_page_width_count": unique_width_count,
        "unique_page_height_count": unique_height_count,
        "page_dimension_consistency_ratio": dim_consistency,

        # Section 11: DOCX structural
        "docx_paragraph_count": docx_p_count,
        "docx_heading_count": docx_h_count,
        "docx_table_count": docx_t_count,
        "docx_image_count": docx_img_count,
        "docx_hyperlink_count": docx_link_count,
        "docx_section_count": docx_sec_count,
        "average_paragraph_length": avg_p_len,
        "average_heading_length": avg_heading_len,
        "table_to_paragraph_ratio": table_to_p_ratio,
        "image_to_paragraph_ratio": img_to_p_ratio,

        # Section 12: Image structural
        "image_width": img_w,
        "image_height": img_h,
        "image_aspect_ratio": aspect_ratio,
        "image_pixel_count": pixel_count,
        "image_color_mode_code": color_mode_code,
        "has_exif": has_exif,
        "exif_field_count": exif_count,
        "image_format_code": image_format_code,
        "resolution_category_code": resolution_cat,
    }
