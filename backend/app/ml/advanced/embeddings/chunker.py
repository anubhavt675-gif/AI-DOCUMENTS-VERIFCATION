"""
Document Text Chunker.
Splits long documents into controlled overlapping chunks for semantic embedding.
"""
from typing import List, Tuple
from app.ml.advanced.config import CHUNK_OVERLAP_CHARS, CHUNK_SIZE_CHARS


class TextChunker:
    """Splits text into overlapping windows while respecting word boundaries."""

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE_CHARS,
        overlap: int = CHUNK_OVERLAP_CHARS,
        **kwargs,
    ):
        chunk_sz = kwargs.get("chunk_size_chars", chunk_size)
        ovlp = kwargs.get("overlap_chars", overlap)
        if ovlp >= chunk_sz:
            raise ValueError(f"Overlap ({ovlp}) must be strictly less than chunk_size ({chunk_sz})")
        self.chunk_size = chunk_sz
        self.overlap = ovlp

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        Returns:
            List of chunk strings
        """
        if not text or not text.strip():
            return ["<EMPTY_TEXT>"]

        cleaned = " ".join(text.split())
        if len(cleaned) <= self.chunk_size:
            return [cleaned]

        chunks: List[str] = []
        step = self.chunk_size - self.overlap
        start = 0

        while start < len(cleaned):
            end = start + self.chunk_size
            chunk = cleaned[start:end]

            # Try to snap to the nearest space if not at text end
            if end < len(cleaned):
                last_space = chunk.rfind(" ")
                if last_space > self.chunk_size // 2:
                    chunk = chunk[:last_space]
                    start += last_space + 1
                else:
                    start += step
            else:
                start += step

            if chunk.strip():
                chunks.append(chunk.strip())

        return chunks
