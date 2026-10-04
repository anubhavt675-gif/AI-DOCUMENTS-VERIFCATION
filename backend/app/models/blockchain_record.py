"""
SQLAlchemy ORM model for blockchain_records table (Phase 6).
Maintains immutable record of document integrity registrations on
Hyperledger Fabric, linking document ID, SHA-256 hash, and IPFS CID.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    document_id = Column(
        String(36),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    blockchain_network = Column(String(100), nullable=False, default="hyperledger-fabric")
    channel_name = Column(String(100), nullable=False, default="documentchannel")
    chaincode_name = Column(String(100), nullable=False, default="documentintegrity")
    transaction_id = Column(String(128), nullable=False, unique=True, index=True)
    document_hash = Column(String(64), nullable=False, index=True)
    hash_algorithm = Column(String(20), nullable=False, default="SHA-256")
    ipfs_cid = Column(String(128), nullable=False, index=True)
    blockchain_status = Column(String(50), nullable=False, default="VALID")
    registered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    block_reference = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    document = relationship("Document", back_populates="blockchain_records")
