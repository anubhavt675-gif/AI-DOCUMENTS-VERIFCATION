"""
Model and artifact serialization utilities.
Uses joblib for scikit-learn models and transformers with strict path sandboxing
and JSON for metadata and schemas.
"""
import json
from pathlib import Path
from typing import Any, Dict
import joblib

from app.ml.config import MODELS_DIR


class SecurityError(Exception):
    """Raised when an unauthorized or out-of-sandbox path is accessed."""
    pass


def validate_path_in_sandbox(path: Path, base_dir: Path = MODELS_DIR) -> Path:
    """
    Ensure the path resolves strictly inside the allowed base directory.
    Prevents path traversal attacks.
    """
    resolved_path = Path(path).resolve()
    resolved_base = Path(base_dir).resolve()
    try:
        resolved_path.relative_to(resolved_base)
    except ValueError:
        raise SecurityError(
            f"Access denied: path '{resolved_path}' is outside sandbox '{resolved_base}'"
        )
    return resolved_path


def save_artifact(obj: Any, file_path: Path, compress: int = 3) -> None:
    """Save Python object using joblib with compression."""
    valid_path = validate_path_in_sandbox(file_path)
    valid_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, valid_path, compress=compress)


def load_artifact(file_path: Path) -> Any:
    """Load serialized Python object from validated path."""
    valid_path = validate_path_in_sandbox(file_path)
    if not valid_path.exists():
        raise FileNotFoundError(f"Artifact not found at {valid_path}")
    return joblib.load(valid_path)


def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save dictionary to JSON file."""
    valid_path = validate_path_in_sandbox(file_path)
    valid_path.parent.mkdir(parents=True, exist_ok=True)
    with open(valid_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON dictionary from file."""
    valid_path = validate_path_in_sandbox(file_path)
    if not valid_path.exists():
        raise FileNotFoundError(f"JSON file not found at {valid_path}")
    with open(valid_path, "r", encoding="utf-8") as f:
        return json.load(f)
