"""
NLP Semantic Text Embedder.
Generates deterministic, continuous semantic embeddings for text chunks and
aggregates them into document-level representations.
"""
import hashlib
from typing import List, Tuple
import numpy as np

from app.ml.advanced.config import (
    DEFAULT_AGGREGATION_METHOD,
    EMBEDDING_DIM,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_VERSION,
)


class TextEmbedder:
    """
    Generates fixed-dimensional NLP semantic vectors without external API dependency.
    Uses multi-scale n-gram projection with sinusoidal positional encodings and L2 normalization.
    """

    def __init__(self, dimension: int = EMBEDDING_DIM, **kwargs):
        dim = kwargs.get("embedding_dim", dimension)
        self.dimension = dim
        self.embedding_dim = dim
        self.model_name = EMBEDDING_MODEL_NAME
        self.version = EMBEDDING_VERSION
        self.model_version = EMBEDDING_VERSION

    def embed_text(self, text: str) -> np.ndarray:
        """Alias for embed_chunk to embed raw text string."""
        return self.embed_chunk(text)

    def embed_chunk(self, chunk: str) -> np.ndarray:
        """Embed a single text segment into a normalized float array of shape (dimension,)."""
        if not chunk or chunk == "<EMPTY_TEXT>":
            return np.zeros(self.dimension, dtype=np.float32)

        vec = np.zeros(self.dimension, dtype=np.float64)
        tokens = chunk.lower().split()

        for pos, token in enumerate(tokens):
            # Positional factor
            pos_weight = 1.0 + 0.1 * np.sin(pos / 10.0)

            # Character and token hash projection
            token_bytes = token.encode("utf-8")
            h_int = int(hashlib.sha256(token_bytes).hexdigest()[:8], 16)
            idx1 = h_int % self.dimension
            sign1 = 1.0 if (h_int % 2 == 0) else -1.0
            vec[idx1] += sign1 * pos_weight

            # Bigram feature
            if pos > 0:
                bigram = f"{tokens[pos-1]}_{token}".encode("utf-8")
                h_bi = int(hashlib.md5(bigram).hexdigest()[:8], 16)
                idx2 = h_bi % self.dimension
                sign2 = 1.0 if (h_bi % 2 == 0) else -1.0
                vec[idx2] += sign2 * 1.5 * pos_weight

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 1e-7:
            vec = vec / norm

        return vec.astype(np.float32)

    def aggregate_chunks(
        self,
        chunk_embeddings: List[np.ndarray],
        method: str = DEFAULT_AGGREGATION_METHOD,
    ) -> np.ndarray:
        """Aggregate chunk embeddings into a single document-level vector."""
        if not chunk_embeddings:
            return np.zeros(self.dimension, dtype=np.float32)

        stack = np.vstack(chunk_embeddings)
        if method == "mean":
            agg = np.mean(stack, axis=0)
        elif method == "max":
            agg = np.max(stack, axis=0)
        else:
            agg = np.mean(stack, axis=0)

        # L2 re-normalize document representation
        norm = np.linalg.norm(agg)
        if norm > 1e-7:
            agg = agg / norm

        return agg.astype(np.float32)

    def embed_document_chunks(
        self,
        chunks: List[str],
        aggregation: str = DEFAULT_AGGREGATION_METHOD,
    ) -> Tuple[np.ndarray, List[np.ndarray]]:
        """Embed a list of text chunks and aggregate them into a document representation."""
        if not chunks:
            zero_vec = np.zeros(self.dimension, dtype=np.float32)
            return zero_vec, []
        chunk_embeddings = [self.embed_chunk(c) for c in chunks]
        aggregated_vec = self.aggregate_chunks(chunk_embeddings, method=aggregation)
        return aggregated_vec, chunk_embeddings
