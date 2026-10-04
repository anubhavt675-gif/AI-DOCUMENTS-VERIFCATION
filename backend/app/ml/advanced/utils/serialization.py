"""
Serialization utilities for PyTorch Autoencoder artifacts and metadata (Phase 5).
"""
import json
from typing import Any
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder handling NumPy scalars, arrays, and special numeric types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


def save_json(data: dict, filepath: str) -> None:
    """Safely saves a dictionary to a JSON file formatted with indentation."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, cls=NumpyEncoder)


def load_json(filepath: str) -> dict:
    """Loads a dictionary from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
