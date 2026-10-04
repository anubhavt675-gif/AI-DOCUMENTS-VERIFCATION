"""
IPFS Service Configuration (Phase 7).
Configures endpoint for local Kubo daemon or embedded content-addressed storage.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
IPFS_STORAGE_DIR = BASE_DIR / "data" / "ipfs_storage"
IPFS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

IPFS_API_URL = os.getenv("IPFS_API_URL", "http://127.0.0.1:5001")
IPFS_GATEWAY_URL = os.getenv("IPFS_GATEWAY_URL", "http://127.0.0.1:8080")
IPFS_TIMEOUT_SECONDS = float(os.getenv("IPFS_TIMEOUT_SECONDS", "10.0"))
