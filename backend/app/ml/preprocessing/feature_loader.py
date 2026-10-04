"""
Feature Loader and Aligner.
Maps raw or stored Phase 3 feature representations into standardized,
deterministic NumPy feature matrices ready for ML training and inference.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.ml.preprocessing.validator import FeatureValidator
from app.services.feature_engineering.feature_registry import FeatureRegistry


class FeatureLoader:
    """Loads and orders feature vectors according to a deterministic schema."""

    def __init__(self, registry: Optional[FeatureRegistry] = None):
        self.registry = registry or FeatureRegistry()
        self.validator = FeatureValidator(self.registry)

    def features_dict_to_array(
        self,
        features: Dict[str, Any],
        ordered_feature_names: List[str],
    ) -> np.ndarray:
        """
        Convert a feature dictionary into a 1D float array strictly aligned
        with ordered_feature_names.
        """
        clean_dict = self.validator.validate_features_dict(features, ordered_feature_names)
        values = [clean_dict[name] for name in ordered_feature_names]
        return np.array(values, dtype=np.float64)

    def load_dataset_from_dicts(
        self,
        records: List[Dict[str, Any]],
        ordered_feature_names: List[str],
    ) -> Tuple[np.ndarray, List[str], Optional[np.ndarray]]:
        """
        Load a list of feature records (e.g. from DB or JSON).
        Each record should contain a 'features' dict or be a flat dict of feature values.
        Returns:
            X: 2D numpy array of shape (N, D)
            doc_ids: list of document_id strings
            y: 1D numpy array of integer labels (if 'label' present), else None
        """
        if not records:
            return np.empty((0, len(ordered_feature_names)), dtype=np.float64), [], None

        X_rows: List[List[float]] = []
        doc_ids: List[str] = []
        labels: List[int] = []
        has_labels = True

        for idx, rec in enumerate(records):
            doc_id = rec.get("document_id", f"doc_{idx}")
            doc_ids.append(str(doc_id))

            # Features might be in rec['features'] or rec directly
            feat_dict = rec.get("features", rec)
            clean_dict = self.validator.validate_features_dict(feat_dict, ordered_feature_names)
            row = [clean_dict[name] for name in ordered_feature_names]
            X_rows.append(row)

            if "label" in rec and rec["label"] is not None:
                labels.append(int(rec["label"]))
            else:
                has_labels = False

        X = np.array(X_rows, dtype=np.float64)
        y = np.array(labels, dtype=np.int32) if has_labels and len(labels) == len(records) else None

        self.validator.validate_matrix(X, expected_dim=len(ordered_feature_names))
        return X, doc_ids, y

    def compute_baseline_statistics(
        self,
        X: np.ndarray,
        ordered_feature_names: List[str],
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute mean and standard deviation for each feature across the training set.
        Used for explainability (calculating deviation of each feature from baseline).
        """
        stats: Dict[str, Dict[str, float]] = {}
        if X.shape[0] == 0:
            for name in ordered_feature_names:
                stats[name] = {"mean": 0.0, "std": 1.0, "min": 0.0, "max": 0.0}
            return stats

        means = np.mean(X, axis=0)
        stds = np.std(X, axis=0)
        mins = np.min(X, axis=0)
        maxs = np.max(X, axis=0)

        for i, name in enumerate(ordered_feature_names):
            stats[name] = {
                "mean": float(means[i]),
                "std": float(stds[i]) if stds[i] > 1e-7 else 1.0,
                "min": float(mins[i]),
                "max": float(maxs[i]),
            }

        return stats
