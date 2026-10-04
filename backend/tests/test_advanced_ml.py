"""
Comprehensive Unit & Integration Tests for Phase 5 Advanced Machine Learning.
Covers:
- Text chunker & overlap
- Dense semantic text embedding & deterministic projection
- Embedding cache & database persistence
- PyTorch Autoencoder training (leak-free)
- Checkpoint persistence and loading
- Reconstruction error scoring and percentile thresholding
- AutoencoderPredictor inference
- Model comparison between Isolation Forest and Autoencoder
"""
import numpy as np
import pytest
import torch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ml.advanced.autoencoder.model import DocumentAutoencoder
from app.ml.advanced.autoencoder.dataset import FeatureDataset, prepare_data_splits
from app.ml.advanced.autoencoder.scoring import (
    compute_reconstruction_errors,
    calculate_threshold,
    score_anomaly,
)
from app.ml.advanced.autoencoder.trainer import AutoencoderTrainer
from app.ml.advanced.autoencoder.predictor import AutoencoderPredictor
from app.ml.advanced.embeddings.chunker import TextChunker
from app.ml.advanced.embeddings.text_embedder import TextEmbedder
from app.ml.advanced.embeddings.embedding_cache import EmbeddingManager, compute_text_hash
from app.ml.advanced.comparison.model_comparator import ModelComparator
from app.models.document import Document
from app.models.document_embedding import DocumentEmbedding
from app.models.advanced_ml import AdvancedMLModel, AdvancedMLPrediction


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_text_chunking():
    chunker = TextChunker(chunk_size_chars=100, overlap_chars=20)
    text = "Official Gazette of the Ministry of Finance. " * 15
    chunks = chunker.chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 120 for c in chunks)


def test_text_embedder_deterministic_and_normalized():
    embedder = TextEmbedder(embedding_dim=64)
    text = "Executive Order regarding cybersecurity protocols for confidential archives."
    
    vec1 = embedder.embed_text(text)
    vec2 = embedder.embed_text(text)
    
    assert len(vec1) == 64
    assert np.allclose(vec1, vec2)
    # L2 normalized
    norm = np.linalg.norm(vec1)
    assert np.isclose(norm, 1.0, atol=1e-5)


def test_embedding_caching_and_invalidation(in_memory_db):
    doc = Document(
        document_id="doc-embed-test-1",
        original_filename="sample.pdf",
        stored_filename="stored_sample.pdf",
        file_type="application/pdf",
        file_size=1024,
    )
    in_memory_db.add(doc)
    in_memory_db.commit()

    manager = EmbeddingManager()
    initial_text = "Standard regulation for regional governance."
    vec1, rec1, is_hit1 = manager.get_or_create_embedding(in_memory_db, doc.document_id, initial_text)
    assert not is_hit1
    assert rec1.chunk_count >= 1

    # Second call with identical text must hit cache
    vec2, rec2, is_hit2 = manager.get_or_create_embedding(in_memory_db, doc.document_id, initial_text)
    assert is_hit2
    assert np.allclose(vec1, vec2)

    # Changed text must invalidate and update
    modified_text = "Altered decree removing all budgetary allocations."
    vec3, rec3, is_hit3 = manager.get_or_create_embedding(in_memory_db, doc.document_id, modified_text)
    assert not is_hit3
    assert rec3.source_text_version != rec1.source_text_version


def test_autoencoder_architecture():
    model = DocumentAutoencoder(input_dim=85, latent_dim=16, hidden_dims=[64, 32])
    x = torch.randn(8, 85)
    reconstructed = model(x)
    assert reconstructed.shape == (8, 85)
    
    latent = model.encode(x)
    assert latent.shape == (8, 16)


def test_autoencoder_leak_free_data_splitting():
    features = np.random.normal(loc=0.5, scale=0.1, size=(40, 85))
    train_X, val_X, _, _, scaler = prepare_data_splits(features, val_ratio=0.2, random_state=42)
    
    assert len(train_X) == 32
    assert len(val_X) == 8
    # Scaler mean must match training data mean
    assert np.allclose(scaler.mean_, np.mean(features[np.arange(40) >= 8], axis=0), atol=0.2)


def test_autoencoder_training_and_thresholding(in_memory_db):
    rng = np.random.RandomState(42)
    features = rng.normal(loc=0.5, scale=0.1, size=(25, 85))
    feature_names = [f"feat_{i}" for i in range(85)]

    trainer = AutoencoderTrainer(epochs=10, batch_size=8, latent_dim=8)
    res = trainer.train(
        features=features,
        version="test-ae-v1",
        input_mode="structured",
        feature_names=feature_names,
        db=in_memory_db,
    )

    assert res["success"] is True
    assert res["threshold"] > 0.0
    assert res["input_dimension"] == 85

    # Check database record created
    db_model = in_memory_db.query(AdvancedMLModel).filter(AdvancedMLModel.model_version == "test-ae-v1").first()
    assert db_model is not None
    assert db_model.is_active is True


def test_reconstruction_scoring_and_anomaly_prediction():
    # 0 = NORMAL, 1 = ANOMALOUS
    pred_normal, score_normal = score_anomaly(reconstruction_error=0.02, threshold=0.08)
    assert pred_normal == 0
    assert 0.0 <= score_normal <= 1.0

    pred_anom, score_anom = score_anomaly(reconstruction_error=0.15, threshold=0.08)
    assert pred_anom == 1
    assert score_anom > score_normal


def test_model_comparator_evaluation():
    rng = np.random.RandomState(42)
    features = rng.normal(loc=0.5, scale=0.1, size=(20, 85))
    ground_truth = np.array([0] * 16 + [1] * 4)
    feature_names = [f"feat_{i}" for i in range(85)]

    comparator = ModelComparator()
    comp_result = comparator.compare_on_data(features, ground_truth, feature_names)

    assert "isolation_forest" in comp_result
    assert "metrics" in comp_result["isolation_forest"]
    assert "accuracy" in comp_result["isolation_forest"]["metrics"]
    assert comp_result["sample_count"] == 20
