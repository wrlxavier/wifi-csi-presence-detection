"""Model evaluation metrics for binary presence detection (0=empty, 1=occupied)."""

from typing import Any
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score


def false_alarm_rate(y_true: Any, y_pred: Any) -> float:
    """False-alarm rate: fraction of empty windows predicted as occupied.

    Equivalent to the false-positive rate with positive class = occupied (1):
    ``FP / (FP + TN)``.

    Returns
    -------
    float
        ``0.0`` if there are no empty (negative) samples.
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    denom = fp + tn
    return float(fp / denom) if denom else 0.0


def compute_metrics(y_true: Any, y_pred: Any) -> dict[str, float]:
    """Standard metrics for the presence detection task.

    Returns
    -------
    dict
        ``accuracy``, ``f1_macro``, and ``false_alarm_rate``.
    """
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
        "false_alarm_rate": false_alarm_rate(y_true, y_pred),
    }
