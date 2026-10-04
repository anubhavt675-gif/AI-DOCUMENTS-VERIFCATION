"""
Phase 3 Test Suite: Feature Engineering, Registry, Validation,
Deterministic Ordering, Reproducibility, Scalers, and API/Dataset Exports.
"""
import io
import os
import tempfile
from pathlib import Path

import docx
import fitz
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test_temp.db"

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.document_analysis import DocumentAnalysis  # noqa: E402
from app.models.document_features import DocumentFeatures  # noqa: E402
from app.services.feature_engineering import (
    FEATURE_VERSION,
    PIPELINE_VERSION,
    FeatureEngineeringPipeline,
    InvalidFeatureVectorError,
    MinMaxScaler,
    PreprocessingIncompleteError,
    StandardScaler,
    default_pipeline,
    feature_registry,
)
from app.services.feature_engineering.file_features import extract_file_features
from app.services.feature_engineering.integrity_features import (
    extract_integrity_and_cross_source_features,
)
from app.services.feature_engineering.metadata_features import extract_metadata_features
from app.services.feature_engineering.structural_features import extract_structural_features
from app.services.feature_engineering.text_features import extract_text_features

SQLALCHEMY_TEST_URL = "sqlite:///./test_temp.db"
test_engine = create_engine(
    SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ── 1. File Features Unit Tests ───────────────────────────────────────────────

class TestFileFeatures:
    def test_file_features_pdf(self):
        feats = extract_file_features(
            original_filename="gov_circular_101.pdf",
            file_type="application/pdf",
            file_size=204800,
            file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            hash_algorithm="SHA-256",
        )
        assert feats["file_size_bytes"] == 204800
        assert feats["file_size_kb"] == 200.0
        assert feats["file_extension_code"] == 1  # PDF code
        assert feats["mime_type_code"] == 1
        assert feats["has_hash"] is True
        assert feats["filename_length"] == len("gov_circular_101.pdf")
        assert feats["filename_digit_count"] == 3
        assert feats["filename_has_uuid_pattern"] is False

    def test_file_features_docx_and_images(self):
        docx_feats = extract_file_features("memo.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 50000, None, None)
        assert docx_feats["file_extension_code"] == 2
        assert docx_feats["has_hash"] is False

        jpg_feats = extract_file_features("badge.jpg", "image/jpeg", 80000, "hash", "SHA-256")
        assert jpg_feats["file_extension_code"] == 4

        png_feats = extract_file_features("diagram.png", "image/png", 120000, "hash", "SHA-256")
        assert png_feats["file_extension_code"] == 5


# ── 2. Text Features Unit Tests ───────────────────────────────────────────────

class TestTextFeatures:
    def test_empty_text_handling(self):
        feats = extract_text_features("")
        assert feats["character_count"] == 0
        assert feats["word_count"] == 0
        assert feats["vocabulary_richness"] == 0.0
        assert feats["empty_text_ratio"] == 1.0

    def test_normal_text_extraction(self):
        text = (
            "The Department of Transportation hereby issues Directive No. 445.\n\n"
            "All regional offices shall implement the security protocols by 2024-11-15.\n"
            "Total allocated budget is $45,000,000."
        )
        feats = extract_text_features(text)
        assert feats["word_count"] > 15
        assert feats["character_count"] > 100
        assert feats["sentence_count"] >= 3
        assert feats["paragraph_count"] >= 2
        assert feats["vocabulary_richness"] > 0.0
        assert feats["detected_date_count"] >= 1
        assert feats["detected_year_count"] >= 1
        assert feats["detected_numeric_value_count"] >= 2
        assert feats["earliest_detected_year"] == 2024

    def test_numeric_and_punctuation_heavy_text(self):
        numeric_text = "100 200 300 400 500 2024 2025 9999"
        num_feats = extract_text_features(numeric_text)
        assert num_feats["numeric_ratio"] > 0.8

        punct_text = "!@#$%^&*()_+=-~`[]{}|:;'<>,.?/"
        punct_feats = extract_text_features(punct_text)
        assert punct_feats["punctuation_ratio"] > 0.9


# ── 3. Metadata Features Unit Tests ──────────────────────────────────────────

class TestMetadataFeatures:
    def test_complete_metadata(self):
        meta = {
            "title": "National Cyber Strategy",
            "author": "Secretariat",
            "subject": "Cyber Security",
            "creator": "GovWriter 3.0",
            "producer": "PrintEngine",
            "keywords": "cyber, defense, infrastructure",
            "created_at": "2023-01-15T10:00:00+00:00",
            "modified_at": "2023-02-20T12:00:00+00:00",
            "last_modified_by": "Secretariat",
        }
        feats = extract_metadata_features(meta)
        assert feats["has_title"] is True
        assert feats["has_author"] is True
        assert feats["author_equals_last_modified_by"] is True
        assert feats["creator_present_and_producer_present"] is True
        assert feats["metadata_modified_after_created"] is True
        assert feats["metadata_creation_year"] == 2023
        assert feats["metadata_completeness_ratio"] == 1.0

    def test_missing_and_partial_metadata(self):
        feats = extract_metadata_features({})
        assert feats["has_title"] is False
        assert feats["metadata_completeness_ratio"] == 0.0
        assert feats["metadata_creation_year"] == 0
        assert feats["metadata_age_days"] == -1.0


# ── 4. Structural Features Unit Tests ────────────────────────────────────────

class TestStructuralFeatures:
    def test_pdf_structural_features(self):
        struct = {
            "format": "PDF",
            "page_count": 5,
            "total_images": 2,
            "total_links": 4,
            "total_text_blocks": 15,
            "font_count": 3,
            "font_names": ["Helvetica", "Times-Roman", "Courier"],
            "font_size_range": {"min": 10.0, "max": 24.0},
            "pages_with_low_text": [3],
            "pages_with_only_images": [5],
            "page_dimensions": [{"page_number": 1, "width": 595.0, "height": 842.0}],
        }
        feats = extract_structural_features(struct, "Sample text")
        assert feats["page_count"] == 5
        assert feats["image_count"] == 2
        assert feats["unique_font_count"] == 3
        assert feats["average_font_size"] == 17.0
        assert feats["minimum_font_size"] == 10.0
        assert feats["maximum_font_size"] == 24.0
        assert feats["image_only_page_ratio"] == 0.2

    def test_docx_structural_features(self):
        struct = {
            "format": "DOCX",
            "paragraph_count": 10,
            "heading_count": 2,
            "headings": ["Intro", "Policy"],
            "table_count": 3,
            "image_count": 1,
            "hyperlink_count": 2,
            "section_count": 1,
        }
        feats = extract_structural_features(struct, "Text content " * 10)
        assert feats["docx_paragraph_count"] == 10
        assert feats["docx_heading_count"] == 2
        assert feats["docx_table_count"] == 3
        assert feats["table_to_paragraph_ratio"] == 0.3


# ── 5. Integrity & Cross-Source Unit Tests ────────────────────────────────────

class TestIntegrityFeatures:
    def test_sha256_hash_validation(self):
        valid_hash = "a" * 64
        feats = extract_integrity_and_cross_source_features(
            file_hash=valid_hash,
            hash_algorithm="SHA-256",
            text_data={"word_count": 100, "paragraph_count": 5},
            metadata={"title": "Test Doc"},
            structure={"page_count": 2},
            ocr_info={"used": False, "status": "not_required"},
        )
        assert feats["sha256_present"] is True
        assert feats["hash_length"] == 64
        assert feats["hash_algorithm_code"] == 1
        assert feats["document_text_present"] is True
        assert feats["metadata_missing"] is False


# ── 6. Normalization & Scaler Unit Tests ──────────────────────────────────────

class TestNormalization:
    def test_minmax_scaler(self):
        data = [
            {"page_count": 1, "word_count": 100},
            {"page_count": 5, "word_count": 500},
            {"page_count": 10, "word_count": 1000},
        ]
        scaler = MinMaxScaler()
        scaler.fit(data)
        transformed = scaler.transform({"page_count": 5, "word_count": 500})
        assert transformed["page_count"] == round(4.0 / 9.0, 6)
        assert transformed["word_count"] == round(400.0 / 900.0, 6)

        # Test state serialization
        state = scaler.to_dict()
        restored = MinMaxScaler.from_dict(state)
        assert restored.data_min == scaler.data_min

    def test_standard_scaler(self):
        data = [
            {"score": 10.0},
            {"score": 20.0},
            {"score": 30.0},
        ]
        scaler = StandardScaler()
        scaler.fit(data)
        transformed = scaler.transform({"score": 20.0})
        # Mean is 20.0, so standardized value should be 0.0
        assert transformed["score"] == 0.0


# ── 7. Reproducibility & Validation ──────────────────────────────────────────

class TestReproducibility:
    def test_deterministic_feature_ordering_and_reproducibility(self):
        # Create mock Document and DocumentAnalysis
        doc = Document(
            document_id="repro-doc-1",
            original_filename="audit.pdf",
            stored_filename="stored_audit.pdf",
            file_type="application/pdf",
            file_size=10240,
            status="uploaded",
            processing_status="completed",
            file_hash="b" * 64,
            hash_algorithm="SHA-256",
        )
        analysis = DocumentAnalysis(
            document_id="repro-doc-1",
            raw_text="Audit Protocol 2024",
            cleaned_text="Audit Protocol 2024",
            word_count=3,
            character_count=19,
            page_count=1,
            image_count=0,
            table_count=0,
            paragraph_count=1,
            metadata_json={"title": "Official Audit"},
            structural_data_json={"page_count": 1, "format": "PDF"},
            ocr_used=False,
            ocr_status="not_required",
        )

        pipeline = FeatureEngineeringPipeline()
        vec1 = pipeline.extract_features(doc, analysis)
        vec2 = pipeline.extract_features(doc, analysis)

        assert vec1.feature_names == vec2.feature_names
        assert vec1.feature_values == vec2.feature_values
        assert vec1.features == vec2.features
        assert len(vec1.feature_names) == feature_registry.get_feature_count()


# ── 8. API Integration Tests ─────────────────────────────────────────────────

class TestFeatureAPIIntegration:
    def test_full_pipeline_to_features_and_export(self, client):
        # 1. Upload a PDF
        doc_fitz = fitz.open()
        p = doc_fitz.new_page()
        p.insert_text((50, 72), "Ministry of Interior Official Gazette No. 2024/99.\nClassified verification authorized.")
        doc_fitz.set_metadata({"title": "Gazette 99", "author": "Ministry"})
        pdf_bytes = doc_fitz.tobytes()
        doc_fitz.close()

        file_tuple = ("file", ("gazette.pdf", io.BytesIO(pdf_bytes), "application/pdf"))
        up_resp = client.post("/api/documents/upload", files=[file_tuple])
        assert up_resp.status_code == 201
        doc_id = up_resp.json()["document_id"]

        # 2. Check feature generation before processing raises 400
        # If background processing hasn't finished, features endpoint should guard against incomplete data
        # We manually process first
        proc_resp = client.post(f"/api/documents/{doc_id}/process")
        assert proc_resp.status_code == 200

        # 3. Generate Features
        feat_gen_resp = client.post(f"/api/documents/{doc_id}/features")
        assert feat_gen_resp.status_code == 200
        gen_data = feat_gen_resp.json()
        assert gen_data["success"] is True
        assert gen_data["feature_version"] == "1.0"
        assert gen_data["feature_count"] > 80

        # 4. Retrieve Features
        feat_get_resp = client.get(f"/api/documents/{doc_id}/features")
        assert feat_get_resp.status_code == 200
        feat_data = feat_get_resp.json()
        assert feat_data["document_id"] == doc_id
        assert feat_data["features"]["word_count"] > 0
        assert feat_data["features"]["sha256_present"] is True

        # 5. Registry inspection endpoint
        reg_resp = client.get("/api/documents/features/registry")
        assert reg_resp.status_code == 200
        assert reg_resp.json()["total_features"] > 80

        # 6. Dataset export JSON
        export_json = client.get("/api/documents/features/dataset?format=json")
        assert export_json.status_code == 200
        assert export_json.json()["total_documents"] >= 1

        # 7. Dataset export CSV
        export_csv = client.get("/api/documents/features/dataset?format=csv")
        assert export_csv.status_code == 200
        assert export_csv.headers["content-type"].startswith("text/csv")
        assert "document_id," in export_csv.text
        assert "file_size_bytes" in export_csv.text

    def test_feature_generation_on_missing_document_returns_404(self, client):
        resp = client.post("/api/documents/00000000-0000-0000-0000-000000000000/features")
        assert resp.status_code == 404

    def test_feature_generation_on_unprocessed_document_returns_400(self, client):
        import uuid
        test_uuid = str(uuid.uuid4())
        # Create an uploaded but unprocessed document directly
        db = TestingSessionLocal()
        doc = Document(
            document_id=test_uuid,
            original_filename="pending.pdf",
            stored_filename="pending.pdf",
            file_type="application/pdf",
            file_size=1024,
            status="uploaded",
            processing_status="pending",
        )
        db.add(doc)
        db.commit()
        db.close()

        resp = client.post(f"/api/documents/{test_uuid}/features")
        assert resp.status_code == 400
        assert "must be completed first" in resp.json()["detail"]
