"""
PyTorch Autoencoder Architecture for Document Anomaly Detection (Phase 5).
Dynamically adapts to input feature dimensions:
- Mode A: Structured features (~85 dimensions)
- Mode B: Structured features + NLP Dense Embeddings (85 + 64 = 149 dimensions)
"""
from typing import List, Optional
import torch
import torch.nn as nn


class DocumentAutoencoder(nn.Module):
    """
    Symmetric Feed-Forward Autoencoder with batch normalization and LeakyReLU activations.
    Reconstruction error (MSE) serves as the basis for anomaly scoring.
    """

    def __init__(
        self,
        input_dim: int,
        latent_dim: int = 16,
        hidden_dims: Optional[List[int]] = None,
        dropout_rate: float = 0.1,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim

        if hidden_dims is None:
            # Dynamically determine intermediate layer dimensions based on input_dim
            if input_dim >= 120:
                hidden_dims = [96, 48]
            elif input_dim >= 60:
                hidden_dims = [64, 32]
            else:
                h1 = max(16, input_dim // 2)
                h2 = max(8, h1 // 2)
                hidden_dims = [h1, h2]

        self.hidden_dims = hidden_dims

        # Build Encoder
        encoder_layers: List[nn.Module] = []
        current_dim = input_dim
        for h_dim in hidden_dims:
            encoder_layers.append(nn.Linear(current_dim, h_dim))
            encoder_layers.append(nn.BatchNorm1d(h_dim))
            encoder_layers.append(nn.LeakyReLU(negative_slope=0.1))
            if dropout_rate > 0.0:
                encoder_layers.append(nn.Dropout(p=dropout_rate))
            current_dim = h_dim

        encoder_layers.append(nn.Linear(current_dim, latent_dim))
        self.encoder = nn.Sequential(*encoder_layers)

        # Build Decoder (symmetric inversion)
        decoder_layers: List[nn.Module] = []
        current_dim = latent_dim
        for h_dim in reversed(hidden_dims):
            decoder_layers.append(nn.Linear(current_dim, h_dim))
            decoder_layers.append(nn.BatchNorm1d(h_dim))
            decoder_layers.append(nn.LeakyReLU(negative_slope=0.1))
            if dropout_rate > 0.0:
                decoder_layers.append(nn.Dropout(p=dropout_rate))
            current_dim = h_dim

        decoder_layers.append(nn.Linear(current_dim, input_dim))
        self.decoder = nn.Sequential(*decoder_layers)

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Projects input space into low-dimensional latent space."""
        return self.encoder(x)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Reconstructs original feature space from latent representation."""
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Full reconstruction forward pass."""
        z = self.encode(x)
        return self.decode(z)
