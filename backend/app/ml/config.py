"""
Machine Learning Configuration.
Defines model directories, default hyperparameters, feature versions,
and project-wide constants for Phase 4 anomaly detection.
"""
import os
from pathlib import Path
from typing import Any, Dict

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models" / "isolation_forest"

# Ensure models directory exists
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Feature and Pipeline Versions
CURRENT_FEATURE_VERSION = "1.0"
CURRENT_PIPELINE_VERSION = "1.0.0"
DEFAULT_MODEL_NAME = "IsolationForest"
DEFAULT_MODEL_VERSION = "1.0.0"

# Hyperparameters for Isolation Forest
DEFAULT_IFOREST_PARAMS: Dict[str, Any] = {
    "n_estimators": 300,
    "max_samples": "auto",
    "contamination": "auto",
    "max_features": 1.0,
    "bootstrap": False,
    "random_state": 42,
    "n_jobs": -1,
}

# Threshold Defaults
DEFAULT_ANOMALY_THRESHOLD = 0.50

# Convention constants
LABEL_NORMAL = 0
LABEL_ANOMALOUS = 1

STATUS_NORMAL = "normal"
STATUS_ANOMALOUS = "anomalous"

# Explainability
TOP_CONTRIBUTING_FEATURES_COUNT = 5

# Standard Legal & Forensic Disclaimer
LEGAL_FORENSIC_DISCLAIMER = (
    "The ML anomaly score reflects statistical divergence from learned document patterns and "
    "does not constitute conclusive or legal proof of document tampering or forgery. "
    "A high anomaly score indicates that the document's extracted feature profile differs "
    "from the baseline training distribution and warrants human or forensic review."
)
