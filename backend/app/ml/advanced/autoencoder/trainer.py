"""
Training pipeline for PyTorch Document Autoencoder (Phase 5).
Guarantees zero data leakage, dynamic layer scaling, and deterministic evaluation.
"""
from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sqlalchemy.orm import Session

from app.ml.advanced.autoencoder.model import DocumentAutoencoder
from app.ml.advanced.autoencoder.dataset import FeatureDataset, prepare_data_splits
from app.ml.advanced.autoencoder.scoring import calculate_threshold, compute_reconstruction_errors
from app.ml.advanced.utils.checkpoint import save_checkpoint
from app.models.advanced_ml import AdvancedMLModel

logger = logging.getLogger(__name__)


class AutoencoderTrainer:
    """Trains, validates, thresholds, and serializes DocumentAutoencoder models."""

    def __init__(
        self,
        learning_rate: float = 0.001,
        weight_decay: float = 1e-5,
        batch_size: int = 32,
        epochs: int = 50,
        latent_dim: int = 16,
        threshold_method: str = "percentile",
        threshold_percentile: float = 95.0,
        random_state: int = 42,
    ):
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.epochs = epochs
        self.latent_dim = latent_dim
        self.threshold_method = threshold_method
        self.threshold_percentile = threshold_percentile
        self.random_state = random_state

    def train(
        self,
        features: np.ndarray,
        version: str,
        input_mode: str,
        feature_names: List[str],
        db: Optional[Session] = None,
        labels: Optional[np.ndarray] = None,
        embedding_version: Optional[str] = None,
        dataset_version: str = "1.0",
    ) -> Dict[str, Any]:
        """
        Executes complete training procedure:
        1. Prepares leak-free data splits (scaler fit on training only)
        2. Initializes dynamic DocumentAutoencoder
        3. Optimizes parameters using MSE reconstruction loss
        4. Calculates decision boundary threshold
        5. Persists artifacts and database records
        """
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)

        start_time = time.time()
        n_samples, input_dim = features.shape

        if n_samples < 5:
            raise ValueError(f"At least 5 samples required for autoencoder training, got {n_samples}")

        # Leak-free splitting
        train_X, val_X, train_y, val_y, scaler = prepare_data_splits(
            features=features,
            labels=labels,
            val_ratio=0.2 if n_samples >= 10 else 0.0,
            random_state=self.random_state,
        )

        train_dataset = FeatureDataset(train_X)
        train_loader = DataLoader(
            train_dataset,
            batch_size=min(self.batch_size, len(train_X)),
            shuffle=True,
        )

        # Initialize network
        model = DocumentAutoencoder(
            input_dim=input_dim,
            latent_dim=min(self.latent_dim, input_dim // 2 or 2),
        )
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )
        criterion = nn.MSELoss()

        # Training loop
        model.train()
        epoch_losses: List[float] = []
        for epoch in range(self.epochs):
            batch_losses = []
            for batch_x in train_loader:
                optimizer.zero_grad()
                reconstructed = model(batch_x)
                loss = criterion(reconstructed, batch_x)
                loss.backward()
                optimizer.step()
                batch_losses.append(loss.item())
            epoch_losses.append(float(np.mean(batch_losses)))

        training_duration = time.time() - start_time

        # Calculate reconstruction errors on training set for thresholding
        train_tensor = torch.tensor(train_X, dtype=torch.float32)
        train_errors = compute_reconstruction_errors(model, train_tensor)

        val_errors = None
        if len(val_X) > 0:
            val_tensor = torch.tensor(val_X, dtype=torch.float32)
            val_errors = compute_reconstruction_errors(model, val_tensor)

        threshold, th_meta = calculate_threshold(
            train_errors=train_errors,
            method=self.threshold_method,
            percentile=self.threshold_percentile,
            val_errors=val_errors,
            val_labels=val_y,
        )

        # Build metadata & schema
        metadata = {
            "model_type": "Autoencoder",
            "model_version": version,
            "input_mode": input_mode,
            "input_dim": input_dim,
            "latent_dim": model.latent_dim,
            "hidden_dims": model.hidden_dims,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "final_train_loss": epoch_losses[-1],
            "training_samples": len(train_X),
            "validation_samples": len(val_X),
            "threshold": threshold,
            "threshold_method": self.threshold_method,
            "threshold_percentile": self.threshold_percentile,
            "training_duration_seconds": round(training_duration, 4),
            "dataset_version": dataset_version,
            "embedding_version": embedding_version or "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        feature_schema = {
            "input_mode": input_mode,
            "feature_dimension": input_dim,
            "feature_names": feature_names,
            "embedding_version": embedding_version,
        }

        # Persist model artifacts
        artifact_dir = save_checkpoint(
            version=version,
            model=model,
            scaler=scaler,
            metadata=metadata,
            feature_schema=feature_schema,
        )

        # Register in database if session provided
        db_record = None
        if db is not None:
            # Check if previous active models should be deactivated
            db.query(AdvancedMLModel).update({AdvancedMLModel.is_active: False})
            db_record = AdvancedMLModel(
                model_name="Autoencoder",
                model_version=version,
                model_type="PyTorch-Autoencoder",
                input_mode=input_mode,
                input_dimension=input_dim,
                threshold=threshold,
                threshold_method=self.threshold_method,
                feature_version="1.0",
                embedding_version=embedding_version or "1.0",
                parameters=metadata,
                training_metrics={
                    "final_loss": epoch_losses[-1],
                    "mean_train_error": float(np.mean(train_errors)),
                    "training_duration": training_duration,
                },
                artifact_path=str(artifact_dir),
                is_active=True,
            )
            db.add(db_record)
            db.commit()
            db.refresh(db_record)

        return {
            "success": True,
            "model_version": version,
            "input_mode": input_mode,
            "input_dimension": input_dim,
            "threshold": threshold,
            "training_duration_seconds": training_duration,
            "artifact_path": str(artifact_dir),
            "db_id": db_record.id if db_record else None,
        }
