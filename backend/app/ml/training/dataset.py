"""
Dataset Preparation and Splitting.
Loads Phase 3 feature vectors from the database or external files,
and performs reproducible train/val/test splits without data leakage.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session

from app.ml.preprocessing.feature_loader import FeatureLoader
from app.models.document_features import DocumentFeatures
from app.services.feature_engineering.feature_registry import FeatureRegistry


class DatasetSplit:
    """Encapsulates dataset partitions."""

    def __init__(
        self,
        X_train: np.ndarray,
        y_train: Optional[np.ndarray],
        doc_ids_train: List[str],
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        doc_ids_val: Optional[List[str]] = None,
        X_test: Optional[np.ndarray] = None,
        y_test: Optional[np.ndarray] = None,
        doc_ids_test: Optional[List[str]] = None,
    ):
        self.X_train = X_train
        self.y_train = y_train
        self.doc_ids_train = doc_ids_train

        self.X_val = X_val if X_val is not None else np.empty((0, X_train.shape[1] if X_train.ndim == 2 else 0))
        self.y_val = y_val
        self.doc_ids_val = doc_ids_val or []

        self.X_test = X_test if X_test is not None else np.empty((0, X_train.shape[1] if X_train.ndim == 2 else 0))
        self.y_test = y_test
        self.doc_ids_test = doc_ids_test or []


class DatasetManager:
    """Prepares and partitions datasets for model training and evaluation."""

    def __init__(self, registry: Optional[FeatureRegistry] = None):
        self.registry = registry or FeatureRegistry()
        self.loader = FeatureLoader(self.registry)

    def load_from_db(
        self,
        db: Session,
        feature_version: str = "1.0",
    ) -> List[Dict[str, Any]]:
        """
        Query all document_features records matching the feature_version.
        """
        records = (
            db.query(DocumentFeatures)
            .filter(DocumentFeatures.feature_version == feature_version)
            .all()
        )
        data: List[Dict[str, Any]] = []
        for r in records:
            data.append({
                "document_id": r.document_id,
                "features": r.features_json,
                "feature_version": r.feature_version,
            })
        return data

    def prepare_dataset(
        self,
        records: List[Dict[str, Any]],
        ordered_feature_names: List[str],
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_state: int = 42,
    ) -> DatasetSplit:
        """
        Extract feature matrices and partition them into train, val, and test splits.
        """
        X, doc_ids, y = self.loader.load_dataset_from_dicts(records, ordered_feature_names)
        n_samples = len(X)

        if n_samples == 0:
            return DatasetSplit(
                X_train=np.empty((0, len(ordered_feature_names))),
                y_train=None,
                doc_ids_train=[],
            )

        # For very small datasets (e.g. < 4 samples in initial development or test cases),
        # keep everything in training so the model has enough points to fit.
        if n_samples < 5:
            return DatasetSplit(
                X_train=X,
                y_train=y,
                doc_ids_train=doc_ids,
            )

        rng = np.random.RandomState(random_state)
        indices = np.arange(n_samples)
        rng.shuffle(indices)

        n_train = max(1, int(round(n_samples * train_ratio)))
        n_val = int(round(n_samples * val_ratio))
        
        train_idx = indices[:n_train]
        val_idx = indices[n_train : n_train + n_val]
        test_idx = indices[n_train + n_val :]

        X_train = X[train_idx]
        doc_ids_train = [doc_ids[i] for i in train_idx]
        y_train = y[train_idx] if y is not None else None

        X_val = X[val_idx] if len(val_idx) > 0 else np.empty((0, X.shape[1]))
        doc_ids_val = [doc_ids[i] for i in val_idx]
        y_val = y[val_idx] if (y is not None and len(val_idx) > 0) else None

        X_test = X[test_idx] if len(test_idx) > 0 else np.empty((0, X.shape[1]))
        doc_ids_test = [doc_ids[i] for i in test_idx]
        y_test = y[test_idx] if (y is not None and len(test_idx) > 0) else None

        return DatasetSplit(
            X_train=X_train,
            y_train=y_train,
            doc_ids_train=doc_ids_train,
            X_val=X_val,
            y_val=y_val,
            doc_ids_val=doc_ids_val,
            X_test=X_test,
            y_test=y_test,
            doc_ids_test=doc_ids_test,
        )
