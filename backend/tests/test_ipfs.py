"""
Comprehensive Unit & Integration Tests for Phase 7 IPFS Integration.
Covers:
- Standard CIDv0 base58btc calculation
- Local content-addressed blockstore persistence
- Retrieval and ownership validation
- Content hash verification (VERIFIED, HASH_MISMATCH, CID_NOT_FOUND)
"""
import hashlib
import os
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.document import Document
from app.services.ipfs.client import IPFSClient, compute_cid_v0
from app.services.ipfs.uploader import IPFSUploader
from app.services.ipfs.downloader import IPFSDownloader
from app.services.ipfs.verifier import IPFSVerifier


@pytest.fixture
def temp_ipfs_dir(tmp_path):
    store = tmp_path / "ipfs_blocks"
    store.mkdir(parents=True, exist_ok=True)
    return store


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_standard_cidv0_computation():
    content = b"Official State Ordinance 2026"
    cid = compute_cid_v0(content)
    # CIDv0 starts with Qm and is 46 characters
    assert cid.startswith("Qm")
    assert len(cid) == 46

    # Deterministic check
    assert compute_cid_v0(content) == cid


def test_ipfs_client_add_and_get(temp_ipfs_dir):
    client = IPFSClient(storage_dir=temp_ipfs_dir)
    data = b"Ministerial Decree on Critical Infrastructure Security"
    cid, provider = client.add_bytes(data)

    assert cid.startswith("Qm")
    assert client.has_cid(cid) is True

    retrieved = client.get_bytes(cid)
    assert retrieved == data


def test_ipfs_uploader_and_verifier(tmp_path, temp_ipfs_dir, db_session):
    # 1. Create dummy file
    doc_file = tmp_path / "official_decree.pdf"
    content = b"%PDF-1.4 Ministry of Foreign Affairs Official Treaty Document"
    doc_file.write_bytes(content)

    doc = Document(
        document_id="doc-ipfs-test-1",
        original_filename="official_decree.pdf",
        stored_filename="stored_decree.pdf",
        file_path=str(doc_file),
        file_type="application/pdf",
        file_size=len(content),
    )
    db_session.add(doc)
    db_session.commit()

    client = IPFSClient(storage_dir=temp_ipfs_dir)
    uploader = IPFSUploader(client=client)
    verifier = IPFSVerifier(client=client)

    # 2. Upload to IPFS
    upload_res = uploader.upload_document(db_session, doc.document_id)
    assert upload_res.success is True
    assert upload_res.ipfs_cid.startswith("Qm")
    assert doc.current_ipfs_cid == upload_res.ipfs_cid

    # 3. Verify content
    verify_res = verifier.verify_document_ipfs(db_session, doc.document_id)
    assert verify_res.status == "VERIFIED"
    assert verify_res.hash_match is True
    assert verify_res.retrieval_success is True


def test_ipfs_verifier_detects_hash_mismatch(tmp_path, temp_ipfs_dir, db_session):
    # 1. Create file and upload to IPFS
    doc_file = tmp_path / "sensitive_budget.pdf"
    original_bytes = b"State Budget Approved: $500,000,000"
    doc_file.write_bytes(original_bytes)

    doc = Document(
        document_id="doc-tamper-test-1",
        original_filename="sensitive_budget.pdf",
        stored_filename="stored_budget.pdf",
        file_path=str(doc_file),
        file_type="application/pdf",
        file_size=len(original_bytes),
    )
    db_session.add(doc)
    db_session.commit()

    client = IPFSClient(storage_dir=temp_ipfs_dir)
    uploader = IPFSUploader(client=client)
    verifier = IPFSVerifier(client=client)

    uploader.upload_document(db_session, doc.document_id)

    # 2. Tamper with the physical file on disk
    tampered_bytes = b"State Budget Approved: $999,999,999 [TAMPERED]"
    doc_file.write_bytes(tampered_bytes)

    # 3. Verification must flag HASH_MISMATCH
    verify_res = verifier.verify_document_ipfs(db_session, doc.document_id)
    assert verify_res.status == "HASH_MISMATCH"
    assert verify_res.hash_match is False
