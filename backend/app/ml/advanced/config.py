"""
Advanced Machine Learning Configuration (Phase 5).
Defines paths, PyTorch Autoencoder architectures, NLP embedding dimensions,
chunking strategies, and thresholding parameters.
"""
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ADVANCED_MODELS_DIR = BASE_DIR / "models" / "autoencoder"
ADVANCED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Autoencoder Hyperparameters
DEFAULT_AUTOENCODER_CONFIG = {
    "hidden_dims": [64, 32],
    "latent_dim": 16,
    "learning_rate": 0.001,
    "batch_size": 16,
    "epochs": 40,
    "weight_decay": 1e-5,
    "threshold_percentile": 95.0,  # 95th percentile reconstruction error as default threshold
}

# NLP Embedding & Chunking Configuration
EMBEDDING_MODEL_NAME = "doc-semantic-embedder-v1"
EMBEDDING_VERSION = "1.0"
EMBEDDING_DIM = 64
CHUNK_SIZE_CHARS = 600
CHUNK_OVERLAP_CHARS = 100
DEFAULT_AGGREGATION_METHOD = "mean"

# Input Modes
INPUT_MODE_STRUCTURED = "structured"  # Phase 3 features only (85-d)
INPUT_MODE_HYBRID = "structured_plus_text_embedding"  # Phase 3 features + NLP embedding (85 + 64 = 149-d)

# Predictions
LABEL_NORMAL = 0
LABEL_ANOMALOUS = 1
STATUS_NORMAL = "normal"
STATUS_ANOMALOUS = "anomalous"


class AdvancedMLConfig:
    BASE_DIR = BASE_DIR
    AUTOENCODER_DIR = ADVANCED_MODELS_DIR
    DEFAULT_CONFIG = DEFAULT_AUTOENCODER_CONFIG
    EMBEDDING_MODEL_NAME = EMBEDDING_MODEL_NAME
    EMBEDDING_VERSION = EMBEDDING_VERSION
    EMBEDDING_DIM = EMBEDDING_DIM
    CHUNK_SIZE_CHARS = CHUNK_SIZE_CHARS
    CHUNK_OVERLAP_CHARS = CHUNK_OVERLAP_CHARS
    DEFAULT_AGGREGATION_METHOD = DEFAULT_AGGREGATION_METHOD
    INPUT_MODE_STRUCTURED = INPUT_MODE_STRUCTURED
    INPUT_MODE_HYBRID = INPUT_MODE_HYBRID
    LABEL_NORMAL = LABEL_NORMAL
    LABEL_ANOMALOUS = LABEL_ANOMALOUS


ADVANCED_ML_CONFIG = AdvancedMLConfig()
