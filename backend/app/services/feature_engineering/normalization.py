"""
Feature normalization module supporting StandardScaler and MinMaxScaler.
Designed for serializable, leak-free preprocessing configurations that can be
fit once on training data and re-applied during inference.
"""
from abc import ABC, abstractmethod
import math
from typing import Any, Dict, List, Optional


class BaseFeatureScaler(ABC):
    """Abstract base class for persistent feature scalers."""

    @abstractmethod
    def fit(self, data_records: List[Dict[str, Any]]) -> "BaseFeatureScaler":
        """Compute normalization parameters from a dataset without data leakage."""
        pass

    @abstractmethod
    def transform(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Normalize a single document's feature dictionary using fitted parameters."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize scaler state to JSON-compatible dictionary."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, state: Dict[str, Any]) -> "BaseFeatureScaler":
        """Restore scaler from serialized state."""
        pass


class StandardScaler(BaseFeatureScaler):
    """
    Standardize features by removing the mean and scaling to unit variance:
    z = (x - u) / s
    """

    def __init__(self, means: Optional[Dict[str, float]] = None, scales: Optional[Dict[str, float]] = None):
        self.means: Dict[str, float] = means or {}
        self.scales: Dict[str, float] = scales or {}

    def fit(self, data_records: List[Dict[str, Any]]) -> "StandardScaler":
        if not data_records:
            return self

        # Collect numeric values for each feature
        feature_vals: Dict[str, List[float]] = {}
        for row in data_records:
            for k, v in row.items():
                if isinstance(v, (int, float, bool)):
                    val = float(v)
                    if not (math.isnan(val) or math.isinf(val)):
                        feature_vals.setdefault(k, []).append(val)

        for k, vals in feature_vals.items():
            if not vals:
                continue
            mean = sum(vals) / float(len(vals))
            variance = sum((x - mean) ** 2 for x in vals) / float(len(vals))
            std = math.sqrt(variance)
            self.means[k] = round(mean, 6)
            self.scales[k] = round(std if std > 1e-7 else 1.0, 6)

        return self

    def transform(self, features: Dict[str, Any]) -> Dict[str, float]:
        normalized: Dict[str, float] = {}
        for k, v in features.items():
            if isinstance(v, (int, float, bool)):
                val = float(v)
                if math.isnan(val) or math.isinf(val):
                    val = 0.0
                mean = self.means.get(k, 0.0)
                scale = self.scales.get(k, 1.0)
                normalized[k] = round((val - mean) / scale, 6)
        return normalized

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "StandardScaler", "means": self.means, "scales": self.scales}

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> "StandardScaler":
        return cls(means=state.get("means", {}), scales=state.get("scales", {}))


class MinMaxScaler(BaseFeatureScaler):
    """
    Transform features by scaling each feature to a given range [0, 1]:
    X_std = (X - X.min) / (X.max - X.min)
    """

    def __init__(self, data_min: Optional[Dict[str, float]] = None, data_max: Optional[Dict[str, float]] = None):
        self.data_min: Dict[str, float] = data_min or {}
        self.data_max: Dict[str, float] = data_max or {}

    def fit(self, data_records: List[Dict[str, Any]]) -> "MinMaxScaler":
        if not data_records:
            return self

        feature_vals: Dict[str, List[float]] = {}
        for row in data_records:
            for k, v in row.items():
                if isinstance(v, (int, float, bool)):
                    val = float(v)
                    if not (math.isnan(val) or math.isinf(val)):
                        feature_vals.setdefault(k, []).append(val)

        for k, vals in feature_vals.items():
            if not vals:
                continue
            mn = min(vals)
            mx = max(vals)
            self.data_min[k] = round(mn, 6)
            self.data_max[k] = round(mx, 6)

        return self

    def transform(self, features: Dict[str, Any]) -> Dict[str, float]:
        normalized: Dict[str, float] = {}
        for k, v in features.items():
            if isinstance(v, (int, float, bool)):
                val = float(v)
                if math.isnan(val) or math.isinf(val):
                    val = 0.0
                mn = self.data_min.get(k, 0.0)
                mx = self.data_max.get(k, 1.0)
                rng = mx - mn
                if rng < 1e-7:
                    normalized[k] = 0.0
                else:
                    normalized[k] = round(max(0.0, min(1.0, (val - mn) / rng)), 6)
        return normalized

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "MinMaxScaler", "data_min": self.data_min, "data_max": self.data_max}

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> "MinMaxScaler":
        return cls(data_min=state.get("data_min", {}), data_max=state.get("data_max", {}))
