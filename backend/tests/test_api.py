"""
Basic API tests for Phase 1.
Run with: pytest tests/ -v

Uses an in-memory SQLite database — no PostgreSQL required.
"""
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Override DATABASE_URL before any app module uses it ──────────────────────
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_temp.db"

from app.main import app           # noqa: E402 — must come after env override
from app.database import get_db, Base  # noqa: E402

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
    from app.models import document  # noqa: F401 — register model metadata
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ── Helper factories ──────────────────────────────────────────────────────────
def make_pdf_file(size_bytes: int = 1024) -> tuple:
    content = b"%PDF-1.4 " + b"0" * size_bytes
    return ("file", ("test.pdf", io.BytesIO(content), "application/pdf"))


def make_disallowed_file() -> tuple:
    return ("file", ("malicious.exe", io.BytesIO(b"bad content"), "application/x-msdownload"))


def make_large_pdf(size_bytes: int) -> tuple:
    content = b"%PDF-1.4 " + b"0" * size_bytes
    return ("file", ("large.pdf", io.BytesIO(content), "application/pdf"))


# ── Health ────────────────────────────────────────────────────────────────────
class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "document-integrity-api"


# ── Upload ────────────────────────────────────────────────────────────────────
class TestUpload:
    def test_valid_pdf_upload(self, client):
        resp = client.post("/api/documents/upload", files=[make_pdf_file()])
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["status"] == "uploaded"
        assert "document_id" in data

    def test_invalid_file_type_rejected(self, client):
        resp = client.post("/api/documents/upload", files=[make_disallowed_file()])
        assert resp.status_code == 400

    def test_oversized_file_rejected(self, client):
        # 55 MB — above the default 50 MB limit
        size = 55 * 1024 * 1024
        resp = client.post("/api/documents/upload", files=[make_large_pdf(size)])
        assert resp.status_code in (400, 413)


# ── Document retrieval ────────────────────────────────────────────────────────
class TestDocumentRetrieval:
    def test_list_documents(self, client):
        resp = client.get("/api/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)

    def test_get_document_by_id(self, client):
        # Upload first
        up = client.post("/api/documents/upload", files=[make_pdf_file()])
        assert up.status_code == 201
        doc_id = up.json()["document_id"]

        resp = client.get(f"/api/documents/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["document_id"] == doc_id

    def test_missing_document_returns_404(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.get(f"/api/documents/{fake_id}")
        assert resp.status_code == 404

    def test_invalid_document_id_returns_404(self, client):
        resp = client.get("/api/documents/not-a-uuid")
        assert resp.status_code == 404
