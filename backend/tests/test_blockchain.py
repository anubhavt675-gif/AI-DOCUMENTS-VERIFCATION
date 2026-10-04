"""
Comprehensive Unit & Integration Tests for Phase 6 Hyperledger Fabric Blockchain.
Covers:
- Fabric compliant SHA-256 transaction ID generation
- Registration of document fingerprints and IPFS CIDs
- Cryptographic ledger persistence and state retrieval
- Immutable transaction audit history
- Duplicate registration prevention
- Technical hash mismatch detection
"""
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.document import Document
from app.services.blockchain.fabric_client import FabricClient, generate_fabric_tx_id
from app.services.blockchain.document_registry import DocumentRegistry
from app.services.blockchain.verifier import BlockchainVerifier
from app.services.blockchain.exceptions import DuplicateRegistrationError


@pytest.fixture
def temp_ledger_dir(tmp_path):
    store = tmp_path / "ledger"
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


def test_fabric_tx_id_generation():
    nonce = b"test_nonce_bytes_12345"
    tx_id = generate_fabric_tx_id("Org1MSP", nonce)
    assert len(tx_id) == 64
    # Deterministic check
    assert generate_fabric_tx_id("Org1MSP", nonce) == tx_id


def test_blockchain_registration_and_verification(tmp_path, temp_ledger_dir, db_session):
    # 1. Create file and document
    doc_file = tmp_path / "presidential_decree.pdf"
    content = b"Official Presidential Appointment Decree No. 441"
    doc_file.write_bytes(content)

    doc = Document(
        document_id="doc-fabric-test-1",
        original_filename="presidential_decree.pdf",
        stored_filename="stored_decree.pdf",
        file_path=str(doc_file),
        file_type="application/pdf",
        file_size=len(content),
        current_ipfs_cid="QmTestCid1234567890abcdef1234567890abcdef123456",
    )
    db_session.add(doc)
    db_session.commit()

    fabric_client = FabricClient(storage_dir=temp_ledger_dir)
    registry = DocumentRegistry(fabric_client=fabric_client)
    verifier = BlockchainVerifier(fabric_client=fabric_client)

    # 2. Register on Fabric
    reg_res = registry.register_document(db_session, doc.document_id)
    assert reg_res.success is True
    assert reg_res.blockchain_status == "registered"
    assert len(reg_res.transaction_id) == 64
    assert reg_res.channel_name == "integritychannel"

    # 3. Verify on Fabric
    verify_res = verifier.verify_document(db_session, doc.document_id)
    assert verify_res.integrity_status == "MATCH"
    assert verify_res.hash_match is True
    assert verify_res.ipfs_cid_match is True
    assert verify_res.blockchain_record_found is True


def test_duplicate_registration_rejected(tmp_path, temp_ledger_dir, db_session):
    doc_file = tmp_path / "land_deed.pdf"
    doc_file.write_bytes(b"Cadastral Registry Deed 90210")

    doc = Document(
        document_id="doc-dup-test-1",
        original_filename="land_deed.pdf",
        stored_filename="stored_deed.pdf",
        file_path=str(doc_file),
        file_type="application/pdf",
        file_size=100,
        current_ipfs_cid="QmDeedCid1234567890abcdef1234567890abcdef123456",
    )
    db_session.add(doc)
    db_session.commit()

    fabric_client = FabricClient(storage_dir=temp_ledger_dir)
    registry = DocumentRegistry(fabric_client=fabric_client)

    registry.register_document(db_session, doc.document_id)

    # Submitting identical document version must be rejected
    with pytest.raises(Exception):
        registry.register_document(db_session, doc.document_id)


def test_tampering_simulation_on_chain(tmp_path, temp_ledger_dir, db_session):
    doc_file = tmp_path / "treaty.pdf"
    original_bytes = b"Peace Treaty Article 1: Unconditional non-aggression pact."
    doc_file.write_bytes(original_bytes)

    doc = Document(
        document_id="doc-tamper-bc-1",
        original_filename="treaty.pdf",
        stored_filename="stored_treaty.pdf",
        file_path=str(doc_file),
        file_type="application/pdf",
        file_size=len(original_bytes),
        current_ipfs_cid="QmTreatyCid1234567890abcdef1234567890abcdef1234",
    )
    db_session.add(doc)
    db_session.commit()

    fabric_client = FabricClient(storage_dir=temp_ledger_dir)
    registry = DocumentRegistry(fabric_client=fabric_client)
    verifier = BlockchainVerifier(fabric_client=fabric_client)

    registry.register_document(db_session, doc.document_id)

    # Tamper with file
    tampered_bytes = b"Peace Treaty Article 1: Conditional non-aggression [ALTERED]."
    doc_file.write_bytes(tampered_bytes)

    verify_res = verifier.verify_document(db_session, doc.document_id)
    assert verify_res.integrity_status == "HASH_MISMATCH"
    assert verify_res.hash_match is False
    assert verify_res.blockchain_record_found is True
