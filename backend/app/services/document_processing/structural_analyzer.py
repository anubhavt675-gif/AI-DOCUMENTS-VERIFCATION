"""
Structural analysis for PDF, DOCX, and Image documents.
Extracts document layout, fonts, tables, images, links, and anomalies like
pages with unusually low text or pages containing only images.
"""
from typing import Any, Dict, List, Optional, Set


def analyze_pdf_structure(
    pages_data: List[Dict[str, Any]],
    total_images: int,
    total_links: int,
    fonts_collected: Set[str],
    font_sizes_collected: List[float],
) -> Dict[str, Any]:
    """
    Produce structured summary for a PDF document.
    """
    page_count = len(pages_data)
    low_text_threshold = 20  # chars

    low_text_pages: List[int] = []
    image_only_pages: List[int] = []
    total_text_blocks = 0
    page_dimensions: List[Dict[str, Any]] = []

    for p in pages_data:
        p_num = p["page_number"]
        txt_len = p.get("text_length", 0)
        img_count = p.get("image_count", 0)
        total_text_blocks += p.get("block_count", 0)

        page_dimensions.append({
            "page_number": p_num,
            "width": round(p.get("width", 0), 2),
            "height": round(p.get("height", 0), 2),
        })

        if img_count > 0 and txt_len == 0:
            image_only_pages.append(p_num)
        elif txt_len < low_text_threshold:
            low_text_pages.append(p_num)

    font_names = sorted(list(fonts_collected))
    font_size_range = None
    if font_sizes_collected:
        font_size_range = {
            "min": round(min(font_sizes_collected), 1),
            "max": round(max(font_sizes_collected), 1),
        }

    return {
        "format": "PDF",
        "page_count": page_count,
        "page_dimensions": page_dimensions,
        "total_text_blocks": total_text_blocks,
        "total_images": total_images,
        "total_links": total_links,
        "font_count": len(font_names),
        "font_names": font_names,
        "font_size_range": font_size_range,
        "pages_with_low_text": low_text_pages,
        "pages_with_only_images": image_only_pages,
    }


def analyze_docx_structure(
    paragraph_count: int,
    heading_count: int,
    headings: List[str],
    table_count: int,
    tables_info: List[Dict[str, int]],
    image_count: int,
    hyperlink_count: int,
) -> Dict[str, Any]:
    """
    Produce structured summary for a DOCX document.
    """
    return {
        "format": "DOCX",
        "paragraph_count": paragraph_count,
        "heading_count": heading_count,
        "headings": headings[:20],  # sample first 20 headings
        "table_count": table_count,
        "tables_info": tables_info,
        "image_count": image_count,
        "hyperlink_count": hyperlink_count,
    }


def analyze_image_structure(
    width: int,
    height: int,
    color_mode: str,
    image_format: str,
    has_exif: bool,
    file_size: int,
) -> Dict[str, Any]:
    """
    Produce structured summary for an image file.
    """
    aspect_ratio = round(width / height, 3) if height > 0 else 0.0
    return {
        "format": image_format.upper(),
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "color_mode": color_mode,
        "has_exif": has_exif,
        "file_size": file_size,
    }
