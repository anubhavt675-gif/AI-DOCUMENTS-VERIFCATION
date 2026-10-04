"""
Checkpoint and artifact persistence manager for PyTorch Autoencoder (Phase 5).
Manages versioned directories:
models/autoencoder/v{version}/
  ├── model.pt
  ├── scaler.joblib
  ├── metadata.json
  └── feature_schema.json
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import torch

from app.ml.advanced.autoencoder.model import DocumentAutoencoder
from app.ml.advanced.utils.serialization import load_json, save_json
from app.ml.advanced.config import ADVANCED_ML_CONFIG


def get_model_dir(version: str) -> Path:
    """Returns absolute path to a specific model version directory."""
    path = ADVANCED_ML_CONFIG.AUTOENCODER_DIR / f"v{version}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_checkpoint(
    version: str,
    model: DocumentAutoencoder,
    scaler: Any,
    metadata: Dict[str, Any],
    feature_schema: Dict[str, Any],
) -> Path:
    """
    Persists all versioned artifacts for an Autoencoder model.
    """
    model_dir = get_model_dir(version)

    # 1. PyTorch weights
    model_path = model_dir / "model.pt"
    torch.save(model.state_dict(), str(model_path))

    # 2. Scaler
    scaler_path = model_dir / "scaler.joblib"
    joblib.dump(scaler, str(scaler_path))

    # 3. Metadata
    meta_path = model_dir / "metadata.json"
    save_json(metadata, str(meta_path))

    # 4. Feature Schema
    schema_path = model_dir / "feature_schema.json"
    save_json(feature_schema, str(schema_path))

    return model_dir


def load_checkpoint(
    version: str,
) -> Tuple[DocumentAutoencoder, Any, Dict[str, Any], Dict[str, Any]]:
    """
    Loads model, scaler, metadata, and feature schema for a specific version.
    """
    model_dir = get_model_dir(version)
    model_path = model_dir / "model.pt"
    scaler_path = model_dir / "scaler.joblib"
    meta_path = model_dir / "metadata.json"
    schema_path = model_dir / "feature_schema.json"

    if not model_path.exists() or not scaler_path.exists():
        raise FileNotFoundError(f"Model artifacts missing for version v{version} at {model_dir}")

    metadata = load_json(str(meta_path))
    schema = load_json(str(schema_path))

    input_dim = metadata.get("input_dim") or schema.get("feature_dimension")
    latent_dim = metadata.get("latent_dim", 16)
    hidden_dims = metadata.get("hidden_dims", None)

    model = DocumentAutoencoder(
        input_dim=input_dim,
        latent_dim=latent_dim,
        hidden_dims=hidden_dims,
    )
    state_dict = torch.load(str(model_path), map_location=torch.device("cpu"))
    model.load_state_dict(state_dict)
    model.eval()

    scaler = joblib.load(str(scaler_path))

    return model, scaler, metadata, schema


def list_saved_versions() -> List[str]:
    """Lists all available saved autoencoder versions."""
    base_dir = ADVANCED_ML_CONFIG.AUTOENCODER_DIR
    if not base_dir.exists():
        return []
    versions = []
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith("v"):
            ver = item.name[1:]
            if (item / "model.pt").exists() and (item / "scaler.joblib").exists():
                versions.append(ver)
    return sorted(versions)
