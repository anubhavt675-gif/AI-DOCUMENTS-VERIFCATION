"""
Embedding Cache and persistence manager (Phase 5).
Ensures embeddings are cached reproducibly based on document_id, source_text_hash,
embedding_model, and embedding_version.
Invalidates or creates new embeddings when text changes.
"""
import hashlib
import logging
from typing import List, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session

from app.models.document_embedding import DocumentEmbedding
from app.ml.advanced.embeddings.text_embedder import TextEmbedder
from app.ml.advanced.embeddings.chunker import TextChunker
from app.ml.advanced.config import ADVANCED_ML_CONFIG

logger = logging.getLogger(__name__)


def compute_text_hash(text: str) -> str:
    """Compute reproducible SHA-256 fingerprint for cleaned source text."""
    normalized = text.strip().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


class EmbeddingManager:
    """Manages chunking, embedding generation, caching, and database retrieval."""

    def __init__(
        self,
        embedder: Optional[TextEmbedder] = None,
        chunker: Optional[TextChunker] = None,
    ):
        self.embedder = embedder or TextEmbedder()
        self.chunker = chunker or TextChunker()

    def get_or_create_embedding(
        self,
        db: Session,
        document_id: str,
        cleaned_text: str,
        force_regenerate: bool = False,
    ) -> Tuple[List[float], DocumentEmbedding, bool]:
        """
        Retrieves cached embedding or generates a new one.
        Returns:
            Tuple of (embedding_vector, db_record, is_cached_hit)
        """
        text_hash = compute_text_hash(cleaned_text or "")
        model_name = self.embedder.model_name
        model_version = self.embedder.model_version
        dim = self.embedder.embedding_dim

        if not force_regenerate:
            existing = (
                db.query(DocumentEmbedding)
                .filter(
                    DocumentEmbedding.document_id == document_id,
                    DocumentEmbedding.embedding_model == model_name,
                    DocumentEmbedding.embedding_version == model_version,
                    DocumentEmbedding.source_text_version == text_hash,
                )
                .first()
            )
            if existing:
                logger.info(f"Embedding cache hit for document {document_id} (hash {text_hash[:8]})")
                return existing.embedding_vector, existing, True

        # Generate chunked embedding
        chunks = self.chunker.chunk_text(cleaned_text or "")
        aggregated_vec, chunk_embeddings = self.embedder.embed_document_chunks(
            chunks, aggregation="mean"
        )

        # Check if an older version exists for this doc & model to update or create
        existing_doc_record = (
            db.query(DocumentEmbedding)
            .filter(
                DocumentEmbedding.document_id == document_id,
                DocumentEmbedding.embedding_model == model_name,
            )
            .first()
        )

        vector_to_store = aggregated_vec.tolist() if isinstance(aggregated_vec, np.ndarray) else aggregated_vec

        record = DocumentEmbedding(
            document_id=document_id,
            embedding_model=model_name,
            embedding_version=model_version,
            source_text_version=text_hash,
            embedding_dimension=dim,
            chunk_count=len(chunks),
            aggregation_method="mean",
            embedding_vector=vector_to_store,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(f"Generated and cached new embedding for document {document_id}")
        return aggregated_vec, record, False
