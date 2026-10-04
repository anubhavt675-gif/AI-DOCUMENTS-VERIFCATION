# Phase 1 Architecture Notes

## Database Schema

```
documents
├── id                  INTEGER PRIMARY KEY
├── document_id         UUID UNIQUE NOT NULL
├── original_filename   VARCHAR(255) NOT NULL
├── stored_filename     VARCHAR(255) NOT NULL
├── file_type           VARCHAR(120) NOT NULL
├── file_size           INTEGER NOT NULL
├── upload_timestamp    TIMESTAMP WITH TIME ZONE
├── status              ENUM(uploaded|processing|verified|suspicious|failed)
├── processing_status   VARCHAR(255) NULLABLE
├── created_at          TIMESTAMP WITH TIME ZONE
└── updated_at          TIMESTAMP WITH TIME ZONE
```

## File Security Pipeline

1. Client sends multipart/form-data POST
2. Backend validates MIME type from Content-Type header
3. Backend validates file extension
4. Backend generates a UUID-based stored filename (user filename never trusted)
5. File is streamed in 64 KB chunks; size checked during write
6. Canonical path is resolved and checked against upload root (path-traversal guard)
7. Database record created only after successful file write

## Future-Compatible Columns (Reserved, Nullable)

These columns are commented out in Phase 1 but will be added via Alembic migrations:

- `ml_score FLOAT` — anomaly confidence score (Phase 3)
- `blockchain_hash VARCHAR(66)` — Ethereum/Hyperledger tx hash (Phase 4)
- `ipfs_cid VARCHAR(255)` — IPFS content identifier (Phase 5)
