"""
Model Evaluation and Metrics Module.
Calculates precision, recall, F1, accuracy, specificity, confusion matrix,
and ROC-AUC from actual ground-truth evaluations. Zero fake numbers.
"""
from typing import Optional
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

from app.ml.config import LABEL_ANOMALOUS, LABEL_NORMAL
from app.ml.schemas import ConfusionMatrixSchema, EvaluationMetricsSchema


class ModelEvaluator:
    """Evaluates anomaly detection performance against ground truth labels."""

    @staticmethod
    def evaluate(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        anomaly_scores: Optional[np.ndarray] = None,
    ) -> EvaluationMetricsSchema:
        """
        Compute evaluation metrics from actual predictions.
        Handles single-class or unbalanced test data gracefully without crashing.
        """
        if len(y_true) == 0:
            return EvaluationMetricsSchema(
                sample_count=0,
                normal_count=0,
                anomalous_count=0,
            )

        normal_count = int(np.sum(y_true == LABEL_NORMAL))
        anomalous_count = int(np.sum(y_true == LABEL_ANOMALOUS))
        sample_count = len(y_true)

        # Standard metrics
        prec = float(precision_score(y_true, y_pred, pos_label=LABEL_ANOMALOUS, zero_division=0))
        rec = float(recall_score(y_true, y_pred, pos_label=LABEL_ANOMALOUS, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, pos_label=LABEL_ANOMALOUS, zero_division=0))
        acc = float(accuracy_score(y_true, y_pred))

        # Confusion Matrix
        cm = confusion_matrix(y_true, y_pred, labels=[LABEL_NORMAL, LABEL_ANOMALOUS])
        tn, fp, fn, tp = [int(v) for v in cm.ravel()]

        # Specificity: TN / (TN + FP)
        specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

        # False Positive Rate: FP / (FP + TN)
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

        # False Negative Rate: FN / (FN + TP)
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

        # ROC-AUC and PR-AUC require at least 2 classes in y_true
        roc_auc: Optional[float] = None
        avg_precision: Optional[float] = None

        if anomaly_scores is not None and len(np.unique(y_true)) > 1:
            try:
                roc_auc = float(roc_auc_score(y_true, anomaly_scores))
            except Exception:
                roc_auc = None

            try:
                avg_precision = float(average_precision_score(y_true, anomaly_scores))
            except Exception:
                avg_precision = None

        return EvaluationMetricsSchema(
            precision=np.round(prec, 4),
            recall=np.round(rec, 4),
            f1_score=np.round(f1, 4),
            accuracy=np.round(acc, 4),
            specificity=np.round(specificity, 4),
            false_positive_rate=np.round(fpr, 4),
            false_negative_rate=np.round(fnr, 4),
            roc_auc=np.round(roc_auc, 4) if roc_auc is not None else None,
            average_precision=np.round(avg_precision, 4) if avg_precision is not None else None,
            sample_count=sample_count,
            normal_count=normal_count,
            anomalous_count=anomalous_count,
            confusion_matrix=ConfusionMatrixSchema(tn=tn, fp=fp, fn=fn, tp=tp),
        )
