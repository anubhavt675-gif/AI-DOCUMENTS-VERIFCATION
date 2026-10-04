"""
Dataset abstractions and preprocessing pipelines for PyTorch Autoencoder (Phase 5).
Guarantees zero data leakage: Scaler is strictly fit on training set only.
"""
from typing import Optional, Tuple
import numpy as np
from app.ml.compat import StandardScaler
import torch
from torch.utils.data import Dataset


class FeatureDataset(Dataset):
    """PyTorch Dataset wrapping scaled document feature vectors."""

    def __init__(self, data: np.ndarray, labels: Optional[np.ndarray] = None):
        self.data = torch.tensor(data, dtype=torch.float32)
        if labels is not None:
            self.labels = torch.tensor(labels, dtype=torch.long)
        else:
            self.labels = None

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int):
        if self.labels is not None:
            return self.data[idx], self.labels[idx]
        return self.data[idx]


def prepare_data_splits(
    features: np.ndarray,
    labels: Optional[np.ndarray] = None,
    val_ratio: float = 0.2,
    random_state: int = 42,
    scaler: Optional[StandardScaler] = None,
) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], Optional[np.ndarray], StandardScaler]:
    """
    Splits feature matrix into train and validation sets, fitting scaler only on training data.
    """
    n_samples = features.shape[0]
    indices = np.arange(n_samples)
    rng = np.random.RandomState(random_state)
    rng.shuffle(indices)

    val_size = int(n_samples * val_ratio)
    val_idx = indices[:val_size]
    train_idx = indices[val_size:]

    train_X = features[train_idx]
    val_X = features[val_idx] if val_size > 0 else np.empty((0, features.shape[1]))

    # Fit scaler strictly on training split
    if scaler is None:
        scaler = StandardScaler()
        train_X_scaled = scaler.fit_transform(train_X)
    else:
        train_X_scaled = scaler.transform(train_X)

    val_X_scaled = scaler.transform(val_X) if val_size > 0 else np.empty((0, features.shape[1]))

    train_y = labels[train_idx] if labels is not None else None
    val_y = labels[val_idx] if (labels is not None and val_size > 0) else None

    return train_X_scaled, val_X_scaled, train_y, val_y, scaler
