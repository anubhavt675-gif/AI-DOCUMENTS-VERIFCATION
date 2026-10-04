"""
SQLAlchemy database engine and session factory.
Engine creation is deferred until first use so test suites can inject
a different database URL before any connection is made.
"""
from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

# Module-level singletons — lazily initialised
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def _get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        url = settings.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        # SQLite (used in tests) doesn't support pool_size / max_overflow
        if url.startswith("sqlite"):
            kwargs: dict = {"connect_args": {"check_same_thread": False}}
        else:
            kwargs = {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}
        _engine = create_engine(url, **kwargs)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine



def _get_session_local() -> sessionmaker:
    _get_engine()  # ensure initialised
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = _get_session_local()()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables defined on Base. Called at startup."""
    from sqlalchemy import inspect, text
    from app.models import (  # noqa: F401 – ensure models are registered
        document,
        document_analysis,
        document_features,
        ml_model,
        ml_prediction,
        document_embedding,
        advanced_ml,
        blockchain_record,
        integrity_verification,
    )
    
    engine = _get_engine()
    Base.metadata.create_all(bind=engine)

    # Safely migrate existing databases where documents table lacked Phase 2-7 columns
    try:
        inspector = inspect(engine)
        if "documents" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("documents")]
            with engine.connect() as conn:
                if "file_path" not in columns:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN file_path VARCHAR(500)"))
                if "file_hash" not in columns:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN file_hash VARCHAR(64)"))
                if "hash_algorithm" not in columns:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN hash_algorithm VARCHAR(20) DEFAULT 'SHA-256'"))
                if "integrity_status" not in columns:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN integrity_status VARCHAR(50) DEFAULT 'UNREGISTERED'"))
                if "current_ipfs_cid" not in columns:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN current_ipfs_cid VARCHAR(128)"))
                if "current_sha256" not in columns:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN current_sha256 VARCHAR(64)"))
                conn.commit()

        if "document_features" in inspector.get_table_names():
            feat_cols = [c["name"] for c in inspector.get_columns("document_features")]
            with engine.connect() as conn:
                if "feature_dimension" not in feat_cols:
                    conn.execute(text("ALTER TABLE document_features ADD COLUMN feature_dimension INTEGER"))
                if "feature_vector" not in feat_cols:
                    conn.execute(text("ALTER TABLE document_features ADD COLUMN feature_vector JSON"))
                conn.commit()
    except Exception:
        pass
