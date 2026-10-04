"""
Unit and Integration Tests for Phase 4: Machine Learning-Based Anomaly Detection.
Covers dataset preparation, data leakage prevention, Isolation Forest training,
persistence, scoring, evaluation metrics, explainability, registry, and APIs.
"""
import os
import uuid
import pytest
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test_temp.db"

from app.database import Base, get_db, _get_engine
from app.main import app
from app.models.document import Document
from app.models.document_features import DocumentFeatures
from app.models.ml_model import MLModel
from app.models.ml_prediction import MLPrediction
from app.ml.anomaly_detection.isolation_forest import IsolationForestDetector
from app.ml.anomaly_detection.scoring import AnomalyScorer
from app.ml.anomaly_detection.threshold import ThresholdManager
from app.ml.model_registry.registry import ModelRegistryService
from app.ml.preprocessing.feature_loader import FeatureLoader
from app.ml.preprocessing.scaler import FeatureScalerWrapper
from app.ml.preprocessing.validator import FeatureValidator
from app.ml.schemas import MLModelConfig, TrainModelRequest
from app.ml.training.dataset import DatasetManager
from app.ml.training.evaluation import ModelEvaluator
from app.ml.training.trainer import ModelTrainer
from app.services.feature_engineering.feature_registry import FeatureRegistry
from app.services.feature_engineering.pipeline import FeatureEngineeringPipeline
from app.services.feature_engineering.exceptions import FeatureValidationError

# Test database setup matching test_temp.db
TEST_DB_URL = "sqlite:///./test_temp.db"
test_engine = _get_engine()
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_feature_record():
    reg = FeatureRegistry()
    features = {f.name: f.default_value for f in reg.list_features()}
    features.update({
        "file_size_bytes": 15000,
        "file_size_kb": 14.65,
        "page_count": 3,
        "word_count": 500,
        "sentence_count": 25,
        "paragraph_count": 8,
        "unique_word_count": 220,
        "vocabulary_richness": 0.44,
        "unique_font_count": 2,
        "metadata_completeness_ratio": 0.75,
        "sha256_present": True,
        "has_hash": True,
    })
    return {
        "document_id": str(uuid.uuid4()),
        "feature_version": "1.0",
        "features": features,
        "feature_names": reg.get_feature_names(),
    }


# ── 1. Dataset & Preprocessing Tests ──────────────────────────────────────────

def test_feature_validator_clean_dict(sample_feature_record):
    validator = FeatureValidator()
    clean = validator.validate_features_dict(sample_feature_record["features"])
    assert isinstance(clean, dict)
    assert len(clean) == FeatureRegistry().get_feature_count()
    for k, v in clean.items():
        assert isinstance(v, float)
        assert not np.isnan(v)
        assert not np.isinf(v)


def test_feature_validator_rejects_nan_and_inf():
    validator = FeatureValidator()
    with pytest.raises(FeatureValidationError):
        validator.validate_features_dict({"page_count": float("nan")})

    with pytest.raises(FeatureValidationError):
        validator.validate_features_dict({"page_count": float("inf")})


def test_data_leakage_prevention_scaler():
    """Ensure scaler fits ONLY on train and transforms test with train parameters."""
    scaler = FeatureScalerWrapper()
    assert not scaler.is_fitted

    with pytest.raises(RuntimeError):
        scaler.transform(np.array([[1.0, 2.0]]))

    X_train = np.array([[10.0, 100.0], [20.0, 200.0], [30.0, 300.0]])
    scaler.fit(X_train)
    assert scaler.is_fitted

    X_test = np.array([[20.0, 200.0]])
    scaled_test = scaler.transform(X_test)
    # The mean of train is [20, 200], so scaled_test should be close to [0, 0]
    np.testing.assert_allclose(scaled_test, [[0.0, 0.0]], atol=1e-5)


def test_dataset_manager_splitting(sample_feature_record):
    records = []
    for i in range(20):
        rec = dict(sample_feature_record)
        rec["document_id"] = f"doc_{i}"
        rec["label"] = 0 if i < 16 else 1
        records.append(rec)

    mgr = DatasetManager()
    split = mgr.prepare_dataset(
        records=records,
        ordered_feature_names=FeatureRegistry().get_feature_names(),
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=42,
    )
    assert len(split.X_train) == 14
    assert len(split.X_val) == 3
    assert len(split.X_test) == 3
    assert split.y_train is not None
    assert len(split.y_train) == 14


# ── 2. Isolation Forest & Scoring Tests ────────────────────────────────────────

def test_isolation_forest_detector_fit_and_predict():
    detector = IsolationForestDetector(n_estimators=50, random_state=42)
    X = np.random.RandomState(42).randn(30, 10)
    detector.fit(X)

    raw_scores = detector.decision_function(X)
    assert len(raw_scores) == 30
    assert isinstance(raw_scores[0], float)

    preds = detector.predict(X)
    assert len(preds) == 30
    # Values must adhere to project convention: 0 (Normal) or 1 (Anomalous)
    assert set(np.unique(preds)).issubset({0, 1})


def test_anomaly_scorer_sigmoid_calibration():
    scorer = AnomalyScorer()
    # Boundary score = 0.0 -> anomaly_score should be 0.50
    assert scorer.compute_anomaly_score(0.0) == 0.50
    # Inlier score > 0 -> anomaly_score < 0.50
    assert scorer.compute_anomaly_score(0.1) < 0.50
    # Outlier score < 0 -> anomaly_score > 0.50
    assert scorer.compute_anomaly_score(-0.1) > 0.50

    pred_norm, stat_norm = scorer.determine_prediction(0.20, threshold=0.50)
    assert pred_norm == 0
    assert stat_norm == "normal"

    pred_anom, stat_anom = scorer.determine_prediction(0.85, threshold=0.50)
    assert pred_anom == 1
    assert stat_anom == "anomalous"


def test_explainable_contributing_features():
    scorer = AnomalyScorer()
    baseline = {
        "page_count": {"mean": 2.0, "std": 0.5},
        "word_count": {"mean": 500.0, "std": 50.0},
        "image_count": {"mean": 1.0, "std": 0.5},
    }
    # An unusual document with 50 pages and 5000 words
    features = {"page_count": 50, "word_count": 5000, "image_count": 1}
    contributions = scorer.compute_contributing_features(features, baseline, top_k=2)

    assert len(contributions) == 2
    # The highest z-scores will be word_count or page_count
    names = [c.feature_name for c in contributions]
    assert "page_count" in names or "word_count" in names
    for c in contributions:
        assert c.deviation_score > 1.0
        assert c.document_value is not None


# ── 3. Evaluation Metrics Tests ───────────────────────────────────────────────

def test_model_evaluator_metrics():
    # Actual test labels: 0=normal, 1=anomalous
    y_true = np.array([0, 0, 0, 0, 1, 1])
    y_pred = np.array([0, 0, 0, 1, 1, 1])  # 3 TN, 1 FP, 0 FN, 2 TP
    scores = np.array([0.1, 0.2, 0.15, 0.6, 0.8, 0.9])

    metrics = ModelEvaluator.evaluate(y_true, y_pred, scores)
    assert metrics.sample_count == 6
    assert metrics.normal_count == 4
    assert metrics.anomalous_count == 2

    assert metrics.confusion_matrix.tn == 3
    assert metrics.confusion_matrix.fp == 1
    assert metrics.confusion_matrix.fn == 0
    assert metrics.confusion_matrix.tp == 2

    # Precision: TP / (TP + FP) = 2 / 3 ~ 0.6667
    assert metrics.precision == pytest.approx(0.6667, abs=1e-3)
    # Recall: TP / (TP + FN) = 2 / 2 = 1.0
    assert metrics.recall == pytest.approx(1.0, abs=1e-3)
    # Specificity: TN / (TN + FP) = 3 / 4 = 0.75
    assert metrics.specificity == pytest.approx(0.75, abs=1e-3)
    assert metrics.roc_auc is not None


# ── 4. End-to-End Trainer & Registry Tests ────────────────────────────────────

def test_trainer_and_registry_flow(db_session, sample_feature_record):
    trainer = ModelTrainer()
    registry_svc = ModelRegistryService()

    # Create dummy records
    records = []
    for i in range(10):
        rec = dict(sample_feature_record)
        rec["document_id"] = f"train_doc_{i}"
        records.append(rec)

    unique_version = f"1.0.test_{uuid.uuid4().hex[:6]}"
    train_req = TrainModelRequest(
        model_name="IsolationForest",
        model_version=unique_version,
        config=MLModelConfig(n_estimators=30, random_state=42),
        set_active=True,
    )
    result = trainer.train(db_session, train_req, dataset_records=records)
    assert result["success"] is True
    assert result["model_version"] == unique_version
    assert result["is_active"] is True

    # Check active model in registry
    active_m = registry_svc.get_active_model(db_session)
    assert active_m is not None
    assert active_m.model_version == unique_version

    # Load active artifacts from memory/disk
    rec, det, sc = registry_svc.load_active_artifacts(db_session)
    assert det.is_fitted
    assert sc.is_fitted


# ── 5. Full REST API Tests ───────────────────────────────────────────────────

def test_api_ml_train_and_inference(client, db_session, sample_feature_record):
    # 1. Setup a Document and DocumentFeatures in DB
    doc_uuid = str(uuid.uuid4())
    doc = Document(
        document_id=doc_uuid,
        original_filename="gov_report.pdf",
        stored_filename="stored_gov_report.pdf",
        file_type="application/pdf",
        file_size=15000,
        status="uploaded",
        processing_status="completed",
        file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    db_session.add(doc)
    db_session.commit()

    features_rec = DocumentFeatures(
        document_id=doc_uuid,
        feature_version="1.0",
        pipeline_version="1.0.0",
        features_json=sample_feature_record["features"],
        feature_names_json=sample_feature_record["feature_names"],
    )
    db_session.add(features_rec)
    db_session.commit()

    # 2. Train model via POST /api/ml/train
    api_model_version = f"1.0.api_test_{uuid.uuid4().hex[:6]}"
    train_resp = client.post(
        "/api/ml/train",
        json={
            "model_name": "IsolationForest",
            "model_version": api_model_version,
            "config": {"n_estimators": 25, "random_state": 42},
            "set_active": True,
        },
    )
    assert train_resp.status_code == 201
    train_data = train_resp.json()
    assert train_data["success"] is True
    assert train_data["model_version"] == api_model_version

    # 3. List models via GET /api/ml/models
    models_resp = client.get("/api/ml/models")
    assert models_resp.status_code == 200
    models_list = models_resp.json()
    assert len(models_list) >= 1
    assert any(m["model_version"] == api_model_version for m in models_list)

    # 4. Get active model via GET /api/ml/models/active
    active_resp = client.get("/api/ml/models/active")
    assert active_resp.status_code == 200
    assert active_resp.json()["model_version"] == api_model_version

    # 5. Predict single document via POST /api/documents/{id}/predict
    pred_resp = client.post(f"/api/documents/{doc_uuid}/predict")
    assert pred_resp.status_code == 200
    pred_data = pred_resp.json()
    assert pred_data["document_id"] == doc_uuid
    assert pred_data["model_name"] == "IsolationForest"
    assert pred_data["prediction"] in (0, 1)
    assert 0.0 <= pred_data["anomaly_score"] <= 1.0
    assert "disclaimer" in pred_data
    assert "statistical divergence" in pred_data["disclaimer"]

    # 6. Retrieve document predictions via GET /api/documents/{id}/predictions
    history_resp = client.get(f"/api/documents/{doc_uuid}/predictions")
    assert history_resp.status_code == 200
    hist = history_resp.json()
    assert len(hist) == 1
    assert hist[0]["document_id"] == doc_uuid

    # 7. Predict batch via POST /api/ml/predict-batch
    batch_resp = client.post("/api/ml/predict-batch", json={"document_ids": [doc_uuid, "invalid-uuid"]})
    assert batch_resp.status_code == 200
    batch_data = batch_resp.json()
    assert batch_data["total_requested"] == 2
    assert batch_data["success_count"] == 1
    assert batch_data["failure_count"] == 1
    assert "invalid-uuid" in batch_data["errors"]

    # 8. Monitoring stats via GET /api/ml/monitoring
    mon_resp = client.get("/api/ml/monitoring")
    assert mon_resp.status_code == 200
    mon_data = mon_resp.json()
    assert mon_data["total_predictions"] >= 1
    assert "average_anomaly_score" in mon_data


def test_predict_document_not_preprocessed_fails(client, db_session):
    unproc_uuid = str(uuid.uuid4())
    doc = Document(
        document_id=unproc_uuid,
        original_filename="raw.pdf",
        stored_filename="raw.pdf",
        file_type="application/pdf",
        file_size=1000,
        status="uploaded",
        processing_status="pending",
    )
    db_session.add(doc)
    db_session.commit()

    resp = client.post(f"/api/documents/{unproc_uuid}/predict")
    assert resp.status_code == 400
    assert "feature engineering" in resp.json()["detail"].lower()
