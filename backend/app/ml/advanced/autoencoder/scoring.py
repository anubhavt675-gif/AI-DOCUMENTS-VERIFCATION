"""
Reconstruction error scoring and threshold strategies for PyTorch Autoencoder (Phase 5).
Adheres strictly to objective technical reporting:
Prediction:
  0 = NORMAL (no statistical anomaly detected)
  1 = ANOMALOUS (statistical anomaly detected)
"""
from typing import Dict, Optional, Tuple
import numpy as np
import torch


def compute_reconstruction_errors(
    model: torch.nn.Module,
    data_tensor: torch.Tensor,
) -> np.ndarray:
    """
    Computes per-sample Mean Squared Error (MSE) reconstruction loss:
    MSE(x, x_hat) = (1 / D) * sum_{j=1}^D (x_j - x_hat_j)^2
    """
    model.eval()
    with torch.no_grad():
        reconstructed = model(data_tensor)
        # Compute squared differences across feature dimensions
        sq_errors = (data_tensor - reconstructed) ** 2
        mse_per_sample = torch.mean(sq_errors, dim=1).cpu().numpy()
    return mse_per_sample


def calculate_threshold(
    train_errors: np.ndarray,
    method: str = "percentile",
    percentile: float = 95.0,
    fixed_value: Optional[float] = None,
    val_errors: Optional[np.ndarray] = None,
    val_labels: Optional[np.ndarray] = None,
) -> Tuple[float, str]:
    """
    Computes decision boundary threshold using one of three strategies:
    1. 'percentile': (100 - alpha)% of baseline training errors
    2. 'validation_f1': Optimize F1 score on validation set if labels exist
    3. 'fixed': User-configured static threshold value
    """
    if method == "fixed" and fixed_value is not None:
        return float(fixed_value), "fixed"

    if method == "validation_f1" and val_errors is not None and val_labels is not None and len(np.unique(val_labels)) > 1:
        # Search candidate thresholds across validation errors
        candidates = np.percentile(val_errors, np.linspace(50, 99, 50))
        best_f1 = -1.0
        best_th = float(np.percentile(train_errors, percentile))

        for cand in candidates:
            preds = (val_errors >= cand).astype(int)
            tp = np.sum((preds == 1) & (val_labels == 1))
            fp = np.sum((preds == 1) & (val_labels == 0))
            fn = np.sum((preds == 0) & (val_labels == 1))
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            if f1 > best_f1:
                best_f1 = f1
                best_th = float(cand)
        return best_th, f1

    # Default robust fallback: Percentile of normal baseline reconstruction errors
    computed_th = float(np.percentile(train_errors, percentile))
    return computed_th, f"percentile_{percentile}"


def score_anomaly(
    reconstruction_error: float,
    threshold: float,
) -> Tuple[int, float]:
    """
    Computes binary prediction and normalized continuous anomaly score in [0.0, 1.0].
    Prediction:
      0 = NORMAL (error < threshold)
      1 = ANOMALOUS (error >= threshold)
    Anomaly score maps error relative to threshold via a smooth sigmoid saturation curve.
    """
    prediction = 1 if reconstruction_error >= threshold else 0

    # Smooth non-linear mapping around threshold:
    # At error == threshold, score is ~ 0.50
    # As error -> 0, score -> 0.0
    # As error >> threshold, score -> 1.0
    if threshold <= 0:
        norm_score = 1.0 if reconstruction_error > 0 else 0.0
    else:
        ratio = reconstruction_error / threshold
        norm_score = float(1.0 / (1.0 + np.exp(-3.0 * (ratio - 1.0))))
        norm_score = round(max(0.0, min(1.0, norm_score)), 4)

    return prediction, norm_score
