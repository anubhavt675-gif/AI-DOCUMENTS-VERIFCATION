"""
Document service layer — database CRUD operations for documents.
Keeps business logic out of the API router.
"""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentCreate


def create_document(db: Session, data: DocumentCreate) -> Document:
    doc = Document(
        document_id=data.document_id,
        original_filename=data.original_filename,
        stored_filename=data.stored_filename,
        file_type=data.file_type,
        file_size=data.file_size,
        status="uploaded",
        processing_status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document_by_document_id(db: Session, document_id: str) -> Optional[Document]:
    return db.query(Document).filter(Document.document_id == str(document_id).strip()).first()


def list_documents(db: Session, skip: int = 0, limit: int = 100) -> tuple[list[Document], int]:
    total = db.query(Document).count()
    docs = (
        db.query(Document)
        .order_by(Document.upload_timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return docs, total
