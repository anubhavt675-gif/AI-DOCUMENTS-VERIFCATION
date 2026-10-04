"""
Rigorous statistical evaluation module for document anomaly detection models (Phase 5).
Calculates real metrics on ground truth validation/test data:
- Precision, Recall, F1, Accuracy, Specificity
- False Positive Rate (FPR), False Negative Rate (FNR)
- ROC-AUC and PR-AUC / Average Precision where applicable
"""
import time
from typing import Any, Dict, List, Optional
import numpy as np
from app.ml.compat import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sqlalchemy.orm import Session

from app.models.advanced_ml import ModelEvaluation


def compute_binary_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Computes complete statistical performance metrics from real test predictions.
    Does not fabricate or smooth numbers.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    # Confusion Matrix: TN, FP, FN, TP
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    roc_auc = None
    pr_auc = None
    if scores is not None and len(np.unique(y_true)) > 1:
        try:
            roc_auc = float(roc_auc_score(y_true, scores))
        except Exception:
            roc_auc = None
        try:
            pr_auc = float(average_precision_score(y_true, scores))
        except Exception:
            pr_auc = None

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "specificity": round(specificity, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
        "pr_auc": round(pr_auc, 4) if pr_auc is not None else None,
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "sample_count": len(y_true),
    }


def evaluate_and_record(
    db: Session,
    model_name: str,
    model_version: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: Optional[np.ndarray] = None,
    evaluation_dataset: str = "benchmark_eval_v1",
    dataset_size: Optional[int] = None,
) -> Dict[str, Any]:
    """Computes metrics and persists the evaluation run into model_evaluations."""
    metrics = compute_binary_metrics(y_true, y_pred, scores)

    eval_record = ModelEvaluation(
        model_name=model_name,
        model_version=model_version,
        evaluation_dataset=evaluation_dataset,
        dataset_size=dataset_size or len(y_true),
        accuracy=metrics["accuracy"],
        precision=metrics["precision"],
        recall=metrics["recall"],
        f1=metrics["f1"],
        specificity=metrics["specificity"],
        false_positive_rate=metrics["false_positive_rate"],
        false_negative_rate=metrics["false_negative_rate"],
        roc_auc=metrics["roc_auc"],
        pr_auc=metrics["pr_auc"],
        confusion_matrix=metrics["confusion_matrix"],
    )
    db.add(eval_record)
    db.commit()
    db.refresh(eval_record)

    result = dict(metrics)
    result["evaluation_id"] = eval_record.id
    return result
