"""Model evaluation helpers: metrics and confusion-matrix plotting.

Shared across the modeling notebooks (04_evaluation, 05_robustness) for the
binary presence task (0 = empty, 1 = occupied).
"""

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score


def false_alarm_rate(y_true, y_pred):
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


def compute_metrics(y_true, y_pred):
    """Standard metrics for the presence task.

    Returns
    -------
    dict
        ``accuracy``, ``f1_macro`` and ``false_alarm_rate``.
    """
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
        "false_alarm_rate": false_alarm_rate(y_true, y_pred),
    }


def plot_confusion_matrix(y_true, y_pred, ax=None, title="Confusion matrix"):
    """Plot a 2x2 confusion-matrix heatmap (empty/occupied).

    Parameters
    ----------
    y_true, y_pred : array-like
        True and predicted binary labels.
    ax : matplotlib.axes.Axes, optional
        Axis to draw on. A new figure/axis is created if omitted.
    title : str
        Plot title.

    Returns
    -------
    matplotlib.axes.Axes
        The axis the heatmap was drawn on.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(4, 3.5))
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    labels = ["empty", "occupied"]
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=labels, yticklabels=labels, ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    return ax
